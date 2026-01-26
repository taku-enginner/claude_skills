---
description: 2枚のスクリーンショットを比較して差分を検出
---

# スクリーンショット比較

比較する画像: $ARGUMENTS

## 実行手順

引数は「before.png after.png」の形式で2つの画像パスを指定してください。

```bash
pip install -q opencv-python numpy Pillow
python .claude_skills/video/compare_screenshots.py $ARGUMENTS -o diff_output -s 0.5
```

実行後、`diff_output/diff_highlight.jpg` を読み込んで:
- 類似度スコア
- 差分がある箇所
- 変更内容の説明
- コスト情報

を報告してください。
