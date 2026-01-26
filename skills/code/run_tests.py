#!/usr/bin/env python3
"""
Flutter Test Runner and Reporter

flutter testを実行し、結果を解析してレポートを生成します。
失敗したテストの情報を詳細に報告し、修正のヒントを提供します。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class TestResult:
    """個別のテスト結果"""
    name: str
    group: str
    status: str  # passed, failed, skipped, error
    duration_ms: int
    error_message: Optional[str]
    stack_trace: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]


@dataclass
class TestReport:
    """テストレポート"""
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_ms: int
    test_results: List[TestResult]
    coverage_percent: Optional[float]
    timestamp: str
    command: str


class FlutterTestRunner:
    """Flutterテスト実行クラス"""

    def __init__(self, project_dir: str = '.'):
        self.project_dir = Path(project_dir)

    def check_flutter(self) -> bool:
        """Flutterが利用可能か確認"""
        try:
            result = subprocess.run(
                ['flutter', '--version'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run_tests(
        self,
        test_path: Optional[str] = None,
        coverage: bool = False,
        reporter: str = 'json'
    ) -> Dict[str, Any]:
        """テストを実行"""
        cmd = ['flutter', 'test']

        if test_path:
            cmd.append(test_path)

        if coverage:
            cmd.append('--coverage')

        # JSON形式で出力（パース用）
        cmd.extend(['--reporter', 'json'])

        print(f"実行コマンド: {' '.join(cmd)}")
        print(f"プロジェクト: {self.project_dir}")
        print("-" * 50)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': ' '.join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'テストがタイムアウトしました（5分）',
                'returncode': -1,
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'command': ' '.join(cmd)
            }

    def parse_json_output(self, output: str) -> List[TestResult]:
        """JSON出力をパース"""
        results = []

        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get('type')

            if event_type == 'testDone':
                test_id = event.get('testID')
                result = event.get('result')
                hidden = event.get('hidden', False)

                if hidden:
                    continue

                # テスト情報を取得
                test_name = event.get('name', f'Test {test_id}')

                # グループ名とテスト名を分離
                parts = test_name.rsplit(' ', 1)
                if len(parts) == 2:
                    group = parts[0]
                    name = parts[1]
                else:
                    group = ''
                    name = test_name

                status = 'passed' if result == 'success' else 'failed'

                results.append(TestResult(
                    name=name,
                    group=group,
                    status=status,
                    duration_ms=event.get('time', 0),
                    error_message=None,
                    stack_trace=None,
                    file_path=None,
                    line_number=None
                ))

            elif event_type == 'error':
                test_id = event.get('testID')
                error = event.get('error', '')
                stack_trace = event.get('stackTrace', '')

                # 対応するテスト結果を更新
                for r in results:
                    if r.status == 'failed':
                        r.error_message = error
                        r.stack_trace = stack_trace

                        # ファイルパスと行番号を抽出
                        match = re.search(r'([^\s]+\.dart):(\d+)', stack_trace)
                        if match:
                            r.file_path = match.group(1)
                            r.line_number = int(match.group(2))
                        break

        return results

    def parse_simple_output(self, output: str, stderr: str) -> List[TestResult]:
        """通常出力をパース（JSONパースに失敗した場合のフォールバック）"""
        results = []

        # 成功パターン
        passed_match = re.search(r'(\d+) tests? passed', output + stderr)
        failed_match = re.search(r'(\d+) tests? failed', output + stderr)

        # エラーメッセージを抽出
        error_blocks = re.findall(
            r'══╡ EXCEPTION CAUGHT.*?═+\n(.*?)(?=══|$)',
            output + stderr,
            re.DOTALL
        )

        # 失敗したテストを抽出
        failure_pattern = re.compile(
            r"Expected: (.*?)\n\s*Actual: (.*?)\n",
            re.MULTILINE
        )

        for match in failure_pattern.finditer(output + stderr):
            results.append(TestResult(
                name='Unknown Test',
                group='',
                status='failed',
                duration_ms=0,
                error_message=f"Expected: {match.group(1)}, Actual: {match.group(2)}",
                stack_trace=None,
                file_path=None,
                line_number=None
            ))

        return results

    def get_coverage(self) -> Optional[float]:
        """カバレッジ情報を取得"""
        coverage_file = self.project_dir / 'coverage' / 'lcov.info'

        if not coverage_file.exists():
            return None

        try:
            with open(coverage_file, 'r') as f:
                content = f.read()

            # LH (lines hit) と LF (lines found) を集計
            lines_hit = sum(int(m) for m in re.findall(r'^LH:(\d+)$', content, re.MULTILINE))
            lines_found = sum(int(m) for m in re.findall(r'^LF:(\d+)$', content, re.MULTILINE))

            if lines_found > 0:
                return round((lines_hit / lines_found) * 100, 2)

        except Exception:
            pass

        return None

    def generate_report(self, run_result: Dict[str, Any], coverage: bool = False) -> TestReport:
        """テストレポートを生成"""
        # 結果をパース
        test_results = self.parse_json_output(run_result['stdout'])

        if not test_results:
            test_results = self.parse_simple_output(
                run_result['stdout'],
                run_result['stderr']
            )

        # 集計
        total = len(test_results)
        passed = sum(1 for r in test_results if r.status == 'passed')
        failed = sum(1 for r in test_results if r.status == 'failed')
        skipped = sum(1 for r in test_results if r.status == 'skipped')
        errors = sum(1 for r in test_results if r.status == 'error')

        # stderrからも情報を取得
        if total == 0:
            # テスト数を直接パース
            match = re.search(r'(\d+) tests? passed', run_result['stdout'] + run_result['stderr'])
            if match:
                passed = int(match.group(1))
                total = passed

            match = re.search(r'(\d+) tests? failed', run_result['stdout'] + run_result['stderr'])
            if match:
                failed = int(match.group(1))
                total += failed

        # 実行時間
        duration_match = re.search(
            r'(\d+):(\d+)',
            run_result['stdout'] + run_result['stderr']
        )
        duration_ms = 0
        if duration_match:
            minutes, seconds = int(duration_match.group(1)), int(duration_match.group(2))
            duration_ms = (minutes * 60 + seconds) * 1000

        # カバレッジ
        coverage_percent = self.get_coverage() if coverage else None

        return TestReport(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_ms=duration_ms,
            test_results=test_results,
            coverage_percent=coverage_percent,
            timestamp=datetime.now().isoformat(),
            command=run_result['command']
        )


def print_report(report: TestReport, verbose: bool = False):
    """レポートを表示"""
    print("\n" + "=" * 60)
    print("テスト実行レポート")
    print("=" * 60)

    # サマリー
    print(f"\n実行日時: {report.timestamp}")
    print(f"コマンド: {report.command}")

    print(f"\n## サマリー")
    print(f"{'─' * 40}")

    if report.total > 0:
        pass_rate = (report.passed / report.total) * 100
    else:
        pass_rate = 0

    status_icon = "✅" if report.failed == 0 else "❌"

    print(f"  {status_icon} 合計: {report.total}件")
    print(f"  ✅ 成功: {report.passed}件")
    print(f"  ❌ 失敗: {report.failed}件")
    if report.skipped > 0:
        print(f"  ⏭️  スキップ: {report.skipped}件")
    if report.errors > 0:
        print(f"  💥 エラー: {report.errors}件")

    print(f"\n  成功率: {pass_rate:.1f}%")

    if report.duration_ms > 0:
        print(f"  実行時間: {report.duration_ms / 1000:.2f}秒")

    if report.coverage_percent is not None:
        print(f"  カバレッジ: {report.coverage_percent}%")

    # 失敗したテストの詳細
    failed_tests = [r for r in report.test_results if r.status == 'failed']

    if failed_tests:
        print(f"\n## 失敗したテスト ({len(failed_tests)}件)")
        print(f"{'─' * 40}")

        for i, test in enumerate(failed_tests, 1):
            print(f"\n  {i}. {test.group} > {test.name}")

            if test.file_path:
                print(f"     📍 {test.file_path}:{test.line_number}")

            if test.error_message:
                # エラーメッセージを整形
                error_lines = test.error_message.strip().split('\n')
                for line in error_lines[:5]:
                    print(f"     ❌ {line}")
                if len(error_lines) > 5:
                    print(f"     ... (他 {len(error_lines) - 5} 行)")

            if verbose and test.stack_trace:
                print(f"\n     スタックトレース:")
                for line in test.stack_trace.strip().split('\n')[:10]:
                    print(f"       {line}")

    # 成功したテスト（verboseの場合のみ）
    if verbose:
        passed_tests = [r for r in report.test_results if r.status == 'passed']
        if passed_tests:
            print(f"\n## 成功したテスト ({len(passed_tests)}件)")
            print(f"{'─' * 40}")
            for test in passed_tests[:20]:
                print(f"  ✅ {test.group} > {test.name}")
            if len(passed_tests) > 20:
                print(f"  ... 他 {len(passed_tests) - 20} 件")

    # 推奨アクション
    if report.failed > 0:
        print(f"\n## 推奨アクション")
        print(f"{'─' * 40}")
        print("  1. 失敗したテストのエラーメッセージを確認")
        print("  2. 該当するソースコードを修正")
        print("  3. テストを再実行して確認")

        if failed_tests and failed_tests[0].file_path:
            print(f"\n  最初に確認すべきファイル:")
            print(f"    {failed_tests[0].file_path}:{failed_tests[0].line_number}")


def print_json_report(report: TestReport):
    """JSON形式でレポートを出力"""
    output = {
        'summary': {
            'total': report.total,
            'passed': report.passed,
            'failed': report.failed,
            'skipped': report.skipped,
            'errors': report.errors,
            'pass_rate': (report.passed / report.total * 100) if report.total > 0 else 0,
            'duration_ms': report.duration_ms,
            'coverage_percent': report.coverage_percent,
        },
        'timestamp': report.timestamp,
        'command': report.command,
        'test_results': [asdict(r) for r in report.test_results],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Flutterテストを実行してレポートを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python run_tests.py
  python run_tests.py test/utils/validator_test.dart
  python run_tests.py --coverage
  python run_tests.py --json
        """
    )
    parser.add_argument("test_path", nargs="?", help="テストファイルまたはディレクトリ")
    parser.add_argument("--project", "-p", default=".", help="Flutterプロジェクトのディレクトリ")
    parser.add_argument("--coverage", "-c", action="store_true", help="カバレッジを計測")
    parser.add_argument("--json", action="store_true", help="JSON形式で出力")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    runner = FlutterTestRunner(args.project)

    # Flutterのチェック
    if not runner.check_flutter():
        print("エラー: Flutterが見つかりません")
        print("flutter コマンドがPATHに含まれていることを確認してください")
        sys.exit(1)

    # テスト実行
    print("テストを実行中...")
    run_result = runner.run_tests(
        test_path=args.test_path,
        coverage=args.coverage
    )

    # レポート生成
    report = runner.generate_report(run_result, coverage=args.coverage)

    # 出力
    if args.json:
        print_json_report(report)
    else:
        print_report(report, verbose=args.verbose)

        # 終了コード
        if report.failed > 0 or report.errors > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
