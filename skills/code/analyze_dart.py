#!/usr/bin/env python3
"""
Dart Code Analyzer for Flutter Test Generation

Dartファイルを解析して、関数・クラス・メソッドの情報を抽出します。
テストケース生成の前段階として使用します。
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class Parameter:
    """関数パラメータ"""
    name: str
    type: Optional[str]
    is_required: bool
    is_named: bool
    default_value: Optional[str]


@dataclass
class Function:
    """関数/メソッド情報"""
    name: str
    return_type: Optional[str]
    parameters: List[Parameter]
    is_async: bool
    is_static: bool
    is_private: bool
    doc_comment: Optional[str]
    line_number: int
    body_preview: str  # 最初の数行


@dataclass
class DartClass:
    """クラス情報"""
    name: str
    is_abstract: bool
    extends: Optional[str]
    implements: List[str]
    mixins: List[str]
    methods: List[Function]
    constructors: List[Function]
    fields: List[dict]
    doc_comment: Optional[str]
    line_number: int


@dataclass
class AnalysisResult:
    """解析結果"""
    file_path: str
    top_level_functions: List[Function]
    classes: List[DartClass]
    imports: List[str]
    part_of: Optional[str]
    errors: List[str]


class DartAnalyzer:
    """Dartコード解析クラス"""

    def __init__(self):
        # 型パターン
        self.type_pattern = r'(?:[\w<>,\s\?]+)'

        # パラメータパターン
        self.param_pattern = re.compile(
            r'(?:(required)\s+)?'  # required キーワード
            r'([\w<>,\?\s]+)?\s*'  # 型
            r'(\w+)'  # パラメータ名
            r'(?:\s*=\s*([^,\}\]]+))?'  # デフォルト値
        )

    def extract_doc_comment(self, lines: List[str], line_idx: int) -> Optional[str]:
        """直前のドキュメントコメントを抽出"""
        comments = []
        idx = line_idx - 1

        while idx >= 0:
            line = lines[idx].strip()
            if line.startswith('///'):
                comments.insert(0, line[3:].strip())
                idx -= 1
            elif line.startswith('/*') or line.endswith('*/') or line.startswith('*'):
                # ブロックコメントは簡易対応
                idx -= 1
            elif line == '':
                idx -= 1
            else:
                break

        return '\n'.join(comments) if comments else None

    def parse_parameters(self, param_str: str) -> List[Parameter]:
        """パラメータ文字列をパース"""
        params = []
        if not param_str or param_str.strip() == '':
            return params

        # 名前付きパラメータ（{}）と位置パラメータ（[]）を分離
        named_match = re.search(r'\{([^}]*)\}', param_str)
        optional_match = re.search(r'\[([^\]]*)\]', param_str)

        # 通常の位置パラメータ
        positional_str = re.sub(r'\{[^}]*\}', '', param_str)
        positional_str = re.sub(r'\[[^\]]*\]', '', positional_str)

        # 位置パラメータをパース
        for part in positional_str.split(','):
            part = part.strip()
            if not part:
                continue

            match = self.param_pattern.match(part)
            if match:
                required, type_str, name, default = match.groups()
                params.append(Parameter(
                    name=name,
                    type=type_str.strip() if type_str else None,
                    is_required=True,
                    is_named=False,
                    default_value=default.strip() if default else None
                ))

        # 名前付きパラメータをパース
        if named_match:
            for part in named_match.group(1).split(','):
                part = part.strip()
                if not part:
                    continue

                is_required = 'required' in part
                part = part.replace('required', '').strip()

                match = self.param_pattern.match(part)
                if match:
                    _, type_str, name, default = match.groups()
                    params.append(Parameter(
                        name=name,
                        type=type_str.strip() if type_str else None,
                        is_required=is_required,
                        is_named=True,
                        default_value=default.strip() if default else None
                    ))

        # オプション位置パラメータをパース
        if optional_match:
            for part in optional_match.group(1).split(','):
                part = part.strip()
                if not part:
                    continue

                match = self.param_pattern.match(part)
                if match:
                    _, type_str, name, default = match.groups()
                    params.append(Parameter(
                        name=name,
                        type=type_str.strip() if type_str else None,
                        is_required=False,
                        is_named=False,
                        default_value=default.strip() if default else None
                    ))

        return params

    def extract_body_preview(self, content: str, start_pos: int, max_lines: int = 5) -> str:
        """関数本体の最初の数行を抽出"""
        # 開始位置から { を探す
        brace_pos = content.find('{', start_pos)
        if brace_pos == -1:
            # アロー関数の場合
            arrow_pos = content.find('=>', start_pos)
            if arrow_pos != -1:
                end_pos = content.find(';', arrow_pos)
                if end_pos != -1:
                    return content[arrow_pos:end_pos + 1].strip()
            return ''

        # { から対応する } までを取得
        depth = 0
        end_pos = brace_pos
        for i, char in enumerate(content[brace_pos:], brace_pos):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break

        body = content[brace_pos:end_pos + 1]
        lines = body.split('\n')[:max_lines]
        return '\n'.join(lines)

    def parse_function(self, match: re.Match, lines: List[str], content: str) -> Function:
        """関数定義をパース"""
        groups = match.groups()

        # グループの構成: (static)?, (async)?, (return_type)?, (name), (params)
        is_static = groups[0] is not None
        is_async = groups[1] is not None
        return_type = groups[2].strip() if groups[2] else None
        name = groups[3]
        params_str = groups[4] if len(groups) > 4 else ''

        # 行番号を計算
        line_number = content[:match.start()].count('\n') + 1

        # ドキュメントコメントを取得
        doc_comment = self.extract_doc_comment(lines, line_number - 1)

        # 本体プレビューを取得
        body_preview = self.extract_body_preview(content, match.end())

        return Function(
            name=name,
            return_type=return_type,
            parameters=self.parse_parameters(params_str),
            is_async=is_async,
            is_static=is_static,
            is_private=name.startswith('_'),
            doc_comment=doc_comment,
            line_number=line_number,
            body_preview=body_preview
        )

    def analyze(self, file_path: str) -> AnalysisResult:
        """Dartファイルを解析"""
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return AnalysisResult(
                file_path=file_path,
                top_level_functions=[],
                classes=[],
                imports=[],
                part_of=None,
                errors=[f"ファイル読み込みエラー: {e}"]
            )

        lines = content.split('\n')

        # import文を抽出
        imports = re.findall(r"import\s+['\"]([^'\"]+)['\"]", content)

        # part of を抽出
        part_of_match = re.search(r"part\s+of\s+['\"]?([^'\";\s]+)", content)
        part_of = part_of_match.group(1) if part_of_match else None

        # トップレベル関数を抽出
        # パターン: (static)? (async)? (type)? functionName(params) { or =>
        function_pattern = re.compile(
            r'^(static\s+)?'  # static
            r'(async\s+)?'  # async
            r'([\w<>,\?\s]+\s+)?'  # 戻り値型
            r'(\w+)\s*'  # 関数名
            r'\(([^)]*)\)\s*'  # パラメータ
            r'(?:async\s*)?'  # async (後置)
            r'[{=]',  # 本体開始
            re.MULTILINE
        )

        top_level_functions = []
        classes = []

        # クラス定義を抽出
        class_pattern = re.compile(
            r'^(abstract\s+)?class\s+(\w+)'
            r'(?:\s+extends\s+([\w<>]+))?'
            r'(?:\s+with\s+([\w<>,\s]+))?'
            r'(?:\s+implements\s+([\w<>,\s]+))?\s*\{',
            re.MULTILINE
        )

        for class_match in class_pattern.finditer(content):
            is_abstract = class_match.group(1) is not None
            class_name = class_match.group(2)
            extends = class_match.group(3)
            mixins = [m.strip() for m in (class_match.group(4) or '').split(',') if m.strip()]
            implements = [i.strip() for i in (class_match.group(5) or '').split(',') if i.strip()]

            line_number = content[:class_match.start()].count('\n') + 1
            doc_comment = self.extract_doc_comment(lines, line_number - 1)

            # クラス本体を取得
            class_start = class_match.end() - 1
            depth = 0
            class_end = class_start
            for i, char in enumerate(content[class_start:], class_start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        class_end = i
                        break

            class_body = content[class_start:class_end + 1]

            # メソッドを抽出
            methods = []
            method_pattern = re.compile(
                r'^\s*(static\s+)?'
                r'(async\s+)?'
                r'([\w<>,\?\s]+\s+)?'
                r'(\w+)\s*'
                r'\(([^)]*)\)\s*'
                r'(?:async\s*)?'
                r'[{=]',
                re.MULTILINE
            )

            for method_match in method_pattern.finditer(class_body):
                method_name = method_match.group(4)
                # コンストラクタは除外
                if method_name == class_name:
                    continue
                # getter/setter も一旦含める
                method = self.parse_function(method_match, lines, class_body)
                method.line_number = line_number + class_body[:method_match.start()].count('\n')
                methods.append(method)

            classes.append(DartClass(
                name=class_name,
                is_abstract=is_abstract,
                extends=extends,
                implements=implements,
                mixins=mixins,
                methods=methods,
                constructors=[],  # 簡略化
                fields=[],  # 簡略化
                doc_comment=doc_comment,
                line_number=line_number
            ))

        # クラス外のトップレベル関数を抽出
        # クラス本体の範囲を除外した部分で関数を探す
        class_ranges = []
        for class_match in class_pattern.finditer(content):
            class_start = class_match.start()
            depth = 0
            class_end = class_match.end()
            for i, char in enumerate(content[class_match.end() - 1:], class_match.end() - 1):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        class_end = i + 1
                        break
            class_ranges.append((class_start, class_end))

        for func_match in function_pattern.finditer(content):
            # クラス内の関数は除外
            in_class = any(start <= func_match.start() < end for start, end in class_ranges)
            if in_class:
                continue

            func = self.parse_function(func_match, lines, content)
            # main関数やビルドメソッドなど一部は除外
            if func.name not in ['main', 'build']:
                top_level_functions.append(func)

        return AnalysisResult(
            file_path=file_path,
            top_level_functions=top_level_functions,
            classes=classes,
            imports=imports,
            part_of=part_of,
            errors=errors
        )


def result_to_dict(result: AnalysisResult) -> dict:
    """AnalysisResultを辞書に変換"""
    return {
        'file_path': result.file_path,
        'top_level_functions': [asdict(f) for f in result.top_level_functions],
        'classes': [
            {
                **asdict(c),
                'methods': [asdict(m) for m in c.methods],
            }
            for c in result.classes
        ],
        'imports': result.imports,
        'part_of': result.part_of,
        'errors': result.errors,
    }


def print_result(result: AnalysisResult):
    """結果を表示"""
    print("=" * 60)
    print(f"Dart解析結果: {result.file_path}")
    print("=" * 60)

    if result.errors:
        print(f"\nエラー:")
        for err in result.errors:
            print(f"  - {err}")

    print(f"\nimport: {len(result.imports)}件")

    if result.top_level_functions:
        print(f"\nトップレベル関数: {len(result.top_level_functions)}件")
        for func in result.top_level_functions:
            params = ', '.join([
                f"{p.type or ''} {p.name}".strip()
                for p in func.parameters
            ])
            async_str = "async " if func.is_async else ""
            return_str = f"{func.return_type} " if func.return_type else ""
            print(f"  - {async_str}{return_str}{func.name}({params}) [line {func.line_number}]")
            if func.doc_comment:
                print(f"      /// {func.doc_comment[:50]}...")

    if result.classes:
        print(f"\nクラス: {len(result.classes)}件")
        for cls in result.classes:
            abstract_str = "abstract " if cls.is_abstract else ""
            extends_str = f" extends {cls.extends}" if cls.extends else ""
            print(f"  - {abstract_str}class {cls.name}{extends_str} [line {cls.line_number}]")

            if cls.methods:
                public_methods = [m for m in cls.methods if not m.is_private]
                private_methods = [m for m in cls.methods if m.is_private]
                print(f"      メソッド: {len(public_methods)}件 (public), {len(private_methods)}件 (private)")

                for method in public_methods[:5]:
                    params = ', '.join([p.name for p in method.parameters])
                    print(f"        - {method.name}({params})")

                if len(public_methods) > 5:
                    print(f"        ... 他 {len(public_methods) - 5}件")

    # テスト対象の候補をサマリー
    testable_functions = [f for f in result.top_level_functions if not f.is_private]
    testable_methods = []
    for cls in result.classes:
        if not cls.is_abstract:
            testable_methods.extend([m for m in cls.methods if not m.is_private])

    print(f"\n" + "-" * 60)
    print(f"テスト対象候補")
    print(f"-" * 60)
    print(f"  トップレベル関数: {len(testable_functions)}件")
    print(f"  クラスメソッド: {len(testable_methods)}件")
    print(f"  合計: {len(testable_functions) + len(testable_methods)}件")


def main():
    parser = argparse.ArgumentParser(
        description="Dartファイルを解析して関数・クラス情報を抽出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python analyze_dart.py lib/utils/validator.dart
  python analyze_dart.py lib/models/user.dart --json
  python analyze_dart.py lib/ --recursive
        """
    )
    parser.add_argument("path", help="Dartファイルまたはディレクトリ")
    parser.add_argument("--json", action="store_true", help="JSON形式で出力")
    parser.add_argument("--recursive", "-r", action="store_true", help="ディレクトリを再帰的に解析")

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"エラー: パスが存在しません: {path}")
        sys.exit(1)

    analyzer = DartAnalyzer()
    results = []

    if path.is_file():
        if not path.suffix == '.dart':
            print(f"エラー: Dartファイルではありません: {path}")
            sys.exit(1)
        results.append(analyzer.analyze(str(path)))
    else:
        # ディレクトリの場合
        pattern = '**/*.dart' if args.recursive else '*.dart'
        dart_files = list(path.glob(pattern))

        if not dart_files:
            print(f"エラー: Dartファイルが見つかりません: {path}")
            sys.exit(1)

        for dart_file in dart_files:
            # テストファイルと生成ファイルは除外
            if '_test.dart' in str(dart_file) or '.g.dart' in str(dart_file):
                continue
            results.append(analyzer.analyze(str(dart_file)))

    if args.json:
        output = [result_to_dict(r) for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print_result(result)
            print()


if __name__ == "__main__":
    main()
