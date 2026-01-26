---
description: Dartファイルからテストコードを自動生成
---

# テスト生成

対象ファイル: $ARGUMENTS

## 実行手順

```bash
# コードを解析
python .claude_skills/code/analyze_dart.py $ARGUMENTS

# テストを生成
python .claude_skills/code/generate_tests.py $ARGUMENTS --force
```

## 生成後

1. 生成されたテストファイルを確認
2. 必要に応じてテストケースを追加・修正
3. `flutter test` で実行確認

## オプション

- `--dry-run`: ファイルを作成せずプレビュー
- `--output <path>`: 出力先を指定
- `--force`: 既存ファイルを上書き
