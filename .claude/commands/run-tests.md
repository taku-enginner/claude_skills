---
description: Flutterテストを実行してレポートを生成
---

# テスト実行

対象: $ARGUMENTS

## 実行手順

```bash
# 指定したテストを実行
python .claude_skills/code/run_tests.py $ARGUMENTS

# カバレッジ付きで実行
python .claude_skills/code/run_tests.py $ARGUMENTS --coverage

# 詳細出力
python .claude_skills/code/run_tests.py $ARGUMENTS --verbose
```

## レポート内容

- 成功/失敗の件数
- 失敗したテストの詳細
- エラーメッセージとスタックトレース
- カバレッジ（オプション）

## 失敗時の対応

テストが失敗した場合:
1. エラーメッセージを確認
2. 該当するソースコードを修正
3. 再テスト

3回失敗したらユーザーに相談すること。
