#!/usr/bin/env python3
"""
Flutter Test Generator

Dartファイルを解析してテストコードを生成します。
analyze_dart.pyの結果を使用してテストケースを生成します。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 同じディレクトリのanalyze_dartをインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_dart import DartAnalyzer, AnalysisResult, Function, DartClass, Parameter


@dataclass
class TestCase:
    """テストケース"""
    name: str
    description: str
    category: str  # normal, boundary, error, security
    input_values: Dict[str, str]
    expected: str
    assertion_type: str  # equals, throws, isTrue, isFalse, isNull, isNotNull


@dataclass
class TestSuite:
    """テストスイート"""
    target_name: str
    target_type: str  # function, method
    class_name: Optional[str]
    test_cases: List[TestCase]
    setup_code: str
    teardown_code: str


class TestGenerator:
    """テストコード生成クラス"""

    def __init__(self):
        # 型に基づくテスト値のサンプル
        self.type_test_values = {
            'String': {
                'normal': ['"valid string"', '"hello world"'],
                'boundary': ['""', '" "', '"a"', '"a" * 1000'],
                'error': ['null'],
                'security': ['"<script>alert(1)</script>"', '"\'; DROP TABLE users;--"'],
            },
            'int': {
                'normal': ['1', '42', '100'],
                'boundary': ['0', '-1', '2147483647', '-2147483648'],
                'error': ['null'],
            },
            'double': {
                'normal': ['1.0', '3.14', '100.5'],
                'boundary': ['0.0', '-0.0', 'double.infinity', 'double.nan'],
                'error': ['null'],
            },
            'bool': {
                'normal': ['true', 'false'],
                'boundary': [],
                'error': ['null'],
            },
            'List': {
                'normal': ['[1, 2, 3]', '["a", "b"]'],
                'boundary': ['[]', '[1]'],
                'error': ['null'],
            },
            'Map': {
                'normal': ['{"key": "value"}', '{"a": 1, "b": 2}'],
                'boundary': ['{}'],
                'error': ['null'],
            },
        }

        # 関数名に基づくテストケース推測
        self.function_patterns = {
            'validate': {'expected_return': 'bool', 'test_true_false': True},
            'is': {'expected_return': 'bool', 'test_true_false': True},
            'has': {'expected_return': 'bool', 'test_true_false': True},
            'can': {'expected_return': 'bool', 'test_true_false': True},
            'check': {'expected_return': 'bool', 'test_true_false': True},
            'parse': {'test_error': True},
            'convert': {'test_error': True},
            'format': {'test_string': True},
            'calculate': {'test_numeric': True},
            'get': {'test_null': True},
            'find': {'test_null': True},
            'fetch': {'test_async': True, 'test_error': True},
            'load': {'test_async': True, 'test_error': True},
            'save': {'test_async': True, 'test_error': True},
            'delete': {'test_async': True, 'test_error': True},
            'create': {'test_error': True},
            'update': {'test_error': True},
        }

    def infer_test_cases(self, func: Function, class_name: Optional[str] = None) -> List[TestCase]:
        """関数からテストケースを推測"""
        test_cases = []

        # 関数名からパターンを推測
        func_lower = func.name.lower()
        patterns = {}
        for pattern, config in self.function_patterns.items():
            if pattern in func_lower:
                patterns.update(config)

        # 戻り値がboolの場合
        if func.return_type == 'bool' or patterns.get('test_true_false'):
            test_cases.extend(self._generate_bool_tests(func))

        # 通常のテストケース
        test_cases.extend(self._generate_normal_tests(func))

        # 境界値テスト
        test_cases.extend(self._generate_boundary_tests(func))

        # エラーテスト
        if patterns.get('test_error') or func.is_async:
            test_cases.extend(self._generate_error_tests(func))

        # セキュリティテスト（文字列入力がある場合）
        has_string_param = any(
            p.type and 'String' in p.type
            for p in func.parameters
        )
        if has_string_param:
            test_cases.extend(self._generate_security_tests(func))

        return test_cases

    def _generate_bool_tests(self, func: Function) -> List[TestCase]:
        """bool戻り値のテストケース"""
        tests = []

        # trueを返すケース
        tests.append(TestCase(
            name=f'{func.name}_正常な入力_trueを返す',
            description=f'{func.name}が正常な入力でtrueを返すことを確認',
            category='normal',
            input_values=self._generate_valid_inputs(func),
            expected='true',
            assertion_type='isTrue'
        ))

        # falseを返すケース
        tests.append(TestCase(
            name=f'{func.name}_不正な入力_falseを返す',
            description=f'{func.name}が不正な入力でfalseを返すことを確認',
            category='normal',
            input_values=self._generate_invalid_inputs(func),
            expected='false',
            assertion_type='isFalse'
        ))

        return tests

    def _generate_normal_tests(self, func: Function) -> List[TestCase]:
        """通常のテストケース"""
        tests = []

        tests.append(TestCase(
            name=f'{func.name}_正常系',
            description=f'{func.name}が正常に動作することを確認',
            category='normal',
            input_values=self._generate_valid_inputs(func),
            expected='/* 期待値を設定 */',
            assertion_type='equals'
        ))

        return tests

    def _generate_boundary_tests(self, func: Function) -> List[TestCase]:
        """境界値テストケース"""
        tests = []

        for param in func.parameters:
            if not param.type:
                continue

            param_type = param.type.replace('?', '').strip()

            if param_type == 'String':
                # 空文字テスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}が空文字',
                    description=f'{param.name}に空文字を渡した場合の動作確認',
                    category='boundary',
                    input_values={param.name: '""'},
                    expected='/* 期待値を設定 */',
                    assertion_type='equals'
                ))

            elif param_type in ['int', 'double', 'num']:
                # ゼロテスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}がゼロ',
                    description=f'{param.name}に0を渡した場合の動作確認',
                    category='boundary',
                    input_values={param.name: '0'},
                    expected='/* 期待値を設定 */',
                    assertion_type='equals'
                ))

                # 負数テスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}が負数',
                    description=f'{param.name}に負数を渡した場合の動作確認',
                    category='boundary',
                    input_values={param.name: '-1'},
                    expected='/* 期待値を設定 */',
                    assertion_type='equals'
                ))

            elif 'List' in param_type:
                # 空リストテスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}が空リスト',
                    description=f'{param.name}に空リストを渡した場合の動作確認',
                    category='boundary',
                    input_values={param.name: '[]'},
                    expected='/* 期待値を設定 */',
                    assertion_type='equals'
                ))

        return tests

    def _generate_error_tests(self, func: Function) -> List[TestCase]:
        """エラーテストケース"""
        tests = []

        # null許容でないパラメータにnullを渡すテスト
        for param in func.parameters:
            if param.type and '?' not in param.type and param.is_required:
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}がnull_例外',
                    description=f'{param.name}にnullを渡すと例外が発生することを確認',
                    category='error',
                    input_values={param.name: 'null'},
                    expected='TypeError',
                    assertion_type='throws'
                ))

        return tests

    def _generate_security_tests(self, func: Function) -> List[TestCase]:
        """セキュリティテストケース"""
        tests = []

        for param in func.parameters:
            if param.type and 'String' in param.type:
                # XSSテスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}にスクリプトタグ',
                    description=f'{param.name}にXSS攻撃文字列を渡した場合の動作確認',
                    category='security',
                    input_values={param.name: '"<script>alert(1)</script>"'},
                    expected='/* サニタイズされるか確認 */',
                    assertion_type='equals'
                ))

                # SQLインジェクションテスト
                tests.append(TestCase(
                    name=f'{func.name}_{param.name}にSQLインジェクション',
                    description=f'{param.name}にSQLインジェクション文字列を渡した場合の動作確認',
                    category='security',
                    input_values={param.name: '"\'; DROP TABLE users;--"'},
                    expected='/* 安全に処理されるか確認 */',
                    assertion_type='equals'
                ))

        return tests

    def _generate_valid_inputs(self, func: Function) -> Dict[str, str]:
        """有効な入力値を生成"""
        inputs = {}
        for param in func.parameters:
            param_type = (param.type or 'dynamic').replace('?', '').strip()

            if param_type in self.type_test_values:
                normal_values = self.type_test_values[param_type]['normal']
                inputs[param.name] = normal_values[0] if normal_values else 'null'
            elif 'String' in param_type:
                inputs[param.name] = '"valid_value"'
            elif param_type in ['int', 'double', 'num']:
                inputs[param.name] = '1'
            elif param_type == 'bool':
                inputs[param.name] = 'true'
            else:
                inputs[param.name] = '/* TODO: 値を設定 */'

        return inputs

    def _generate_invalid_inputs(self, func: Function) -> Dict[str, str]:
        """無効な入力値を生成"""
        inputs = {}
        for param in func.parameters:
            param_type = (param.type or 'dynamic').replace('?', '').strip()

            if 'String' in param_type:
                inputs[param.name] = '""'  # 空文字
            elif param_type in ['int', 'double', 'num']:
                inputs[param.name] = '-1'  # 負数
            elif param_type == 'bool':
                inputs[param.name] = 'false'
            else:
                inputs[param.name] = 'null'

        return inputs

    def generate_test_code(self, result: AnalysisResult) -> str:
        """テストコードを生成"""
        lines = []

        # ヘッダー
        lines.append("import 'package:flutter_test/flutter_test.dart';")

        # 対象ファイルのimport
        # lib/xxx.dart → package:app_name/xxx.dart に変換
        source_path = result.file_path
        if 'lib/' in source_path:
            relative_path = source_path.split('lib/')[-1]
            lines.append(f"import 'package:app_name/{relative_path}';")
        else:
            lines.append(f"import '{source_path}';")

        lines.append("")
        lines.append("void main() {")

        # トップレベル関数のテスト
        for func in result.top_level_functions:
            if func.is_private:
                continue

            lines.append(f"  group('{func.name}', () {{")

            test_cases = self.infer_test_cases(func)
            for tc in test_cases:
                lines.extend(self._generate_test_block(tc, func))

            lines.append("  });")
            lines.append("")

        # クラスのテスト
        for cls in result.classes:
            if cls.is_abstract:
                continue

            lines.append(f"  group('{cls.name}', () {{")

            # セットアップ
            lines.append(f"    late {cls.name} sut;")
            lines.append("")
            lines.append("    setUp(() {")
            lines.append(f"      sut = {cls.name}();  // TODO: 適切な初期化")
            lines.append("    });")
            lines.append("")

            for method in cls.methods:
                if method.is_private:
                    continue

                lines.append(f"    group('{method.name}', () {{")

                test_cases = self.infer_test_cases(method, cls.name)
                for tc in test_cases:
                    lines.extend(self._generate_test_block(tc, method, is_method=True))

                lines.append("    });")
                lines.append("")

            lines.append("  });")
            lines.append("")

        lines.append("}")

        return '\n'.join(lines)

    def _generate_test_block(self, tc: TestCase, func: Function, is_method: bool = False) -> List[str]:
        """個別のテストブロックを生成"""
        lines = []
        indent = "      " if is_method else "    "

        # テスト関数
        async_str = "async " if func.is_async else ""
        lines.append(f"{indent}test('{tc.name}', () {async_str}{{")

        # Arrange
        lines.append(f"{indent}  // Arrange")
        for param_name, value in tc.input_values.items():
            lines.append(f"{indent}  final {param_name} = {value};")

        lines.append("")

        # Act
        lines.append(f"{indent}  // Act")
        params = ', '.join([
            f'{p.name}: {p.name}' if p.is_named else p.name
            for p in func.parameters
        ])

        if is_method:
            call = f"sut.{func.name}({params})"
        else:
            call = f"{func.name}({params})"

        if func.is_async:
            call = f"await {call}"

        if tc.assertion_type == 'throws':
            lines.append(f"{indent}  // Assert")
            lines.append(f"{indent}  expect(() => {call}, throwsA(isA<{tc.expected}>()));")
        else:
            lines.append(f"{indent}  final result = {call};")
            lines.append("")

            # Assert
            lines.append(f"{indent}  // Assert")
            if tc.assertion_type == 'isTrue':
                lines.append(f"{indent}  expect(result, isTrue);")
            elif tc.assertion_type == 'isFalse':
                lines.append(f"{indent}  expect(result, isFalse);")
            elif tc.assertion_type == 'isNull':
                lines.append(f"{indent}  expect(result, isNull);")
            elif tc.assertion_type == 'isNotNull':
                lines.append(f"{indent}  expect(result, isNotNull);")
            else:
                lines.append(f"{indent}  expect(result, equals({tc.expected}));")

        lines.append(f"{indent}}});")
        lines.append("")

        return lines

    def get_test_file_path(self, source_path: str) -> str:
        """ソースファイルからテストファイルパスを生成"""
        path = Path(source_path)

        # lib/xxx.dart → test/xxx_test.dart
        if 'lib/' in str(path):
            relative = str(path).split('lib/')[-1]
            test_path = f"test/{relative.replace('.dart', '_test.dart')}"
        else:
            test_path = str(path).replace('.dart', '_test.dart')

        return test_path


def print_summary(result: AnalysisResult, test_cases_count: int, test_file: str):
    """サマリーを表示"""
    print("=" * 60)
    print("テスト生成完了")
    print("=" * 60)

    print(f"\n対象ファイル: {result.file_path}")
    print(f"生成先: {test_file}")

    # カウント
    func_count = len([f for f in result.top_level_functions if not f.is_private])
    method_count = sum(
        len([m for m in c.methods if not m.is_private])
        for c in result.classes if not c.is_abstract
    )

    print(f"\nテスト対象:")
    print(f"  トップレベル関数: {func_count}件")
    print(f"  クラスメソッド: {method_count}件")
    print(f"\n生成したテストケース: {test_cases_count}件")

    print(f"\n次のステップ:")
    print(f"  1. {test_file} を確認・修正")
    print(f"  2. flutter test {test_file} で実行")


def main():
    parser = argparse.ArgumentParser(
        description="Dartファイルからテストコードを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate_tests.py lib/utils/validator.dart
  python generate_tests.py lib/models/user.dart --output test/models/user_test.dart
  python generate_tests.py lib/utils/validator.dart --dry-run
        """
    )
    parser.add_argument("source", help="対象のDartファイル")
    parser.add_argument("--output", "-o", help="出力先（指定しない場合は自動生成）")
    parser.add_argument("--dry-run", action="store_true", help="ファイルを作成せず内容を表示")
    parser.add_argument("--force", "-f", action="store_true", help="既存ファイルを上書き")

    args = parser.parse_args()

    source_path = Path(args.source)

    if not source_path.exists():
        print(f"エラー: ファイルが存在しません: {source_path}")
        sys.exit(1)

    if not source_path.suffix == '.dart':
        print(f"エラー: Dartファイルではありません: {source_path}")
        sys.exit(1)

    # 解析
    analyzer = DartAnalyzer()
    result = analyzer.analyze(str(source_path))

    if result.errors:
        print(f"警告: 解析エラーがあります:")
        for err in result.errors:
            print(f"  - {err}")

    # テスト生成
    generator = TestGenerator()
    test_code = generator.generate_test_code(result)

    # テストケース数をカウント
    test_cases_count = test_code.count("test('")

    # 出力先を決定
    if args.output:
        test_file = args.output
    else:
        test_file = generator.get_test_file_path(str(source_path))

    if args.dry_run:
        print(f"// 生成先: {test_file}")
        print("// " + "=" * 58)
        print(test_code)
        print_summary(result, test_cases_count, test_file)
    else:
        # ディレクトリを作成
        test_path = Path(test_file)
        test_path.parent.mkdir(parents=True, exist_ok=True)

        # 既存ファイルのチェック
        if test_path.exists() and not args.force:
            print(f"エラー: ファイルが既に存在します: {test_file}")
            print("上書きする場合は --force オプションを使用してください")
            sys.exit(1)

        # ファイルに書き込み
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)

        print_summary(result, test_cases_count, test_file)
        print(f"\nファイルを作成しました: {test_file}")


if __name__ == "__main__":
    main()
