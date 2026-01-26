# スクリーンショット差分比較 使い方ガイド

2枚のスクリーンショットを比較し、差分をハイライト表示するツールです。

## 用途

- **回帰テスト**: 変更前後のUIを比較
- **PRレビュー**: UI変更の影響範囲を確認
- **バグ検証**: 修正前後の画面を比較

---

## 基本的な使い方

```bash
python compare_screenshots.py before.png after.png
```

出力:
```
比較中...
  変更前: before.png (1080x1920)
  変更後: after.png (1080x1920)

==================================================
比較完了!
==================================================

類似度: 94.5% △ ほぼ同じ（軽微な差分あり）
差分領域数: 3箇所

差分領域の詳細:
  1. 位置(120, 450) サイズ(200x50)
  2. 位置(50, 800) サイズ(300x100)
  3. 位置(400, 1200) サイズ(150x80)

出力ファイル:
  - side_by_side: diff_output/diff_side_by_side.jpg
  - highlight: diff_output/diff_highlight.jpg
  - diff_only: diff_output/diff_only.jpg
  - blend: diff_output/diff_blend.jpg

Claudeに渡す推奨ファイル:
  diff_output/diff_highlight.jpg
```

---

## 出力ファイル

| ファイル | 説明 | 用途 |
|----------|------|------|
| `diff_side_by_side.jpg` | 左右に並べた比較 | 全体を俯瞰 |
| `diff_highlight.jpg` | 差分をマゼンタでハイライト | **Claudeに渡す推奨** |
| `diff_only.jpg` | 差分部分のみ表示 | 変更箇所の詳細確認 |
| `diff_blend.jpg` | 2枚を半透明で重ねる | 位置ずれの確認 |

---

## オプション

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ディレクトリ | diff_output |
| `-s, --scale` | 出力画像のスケール | 1.0 |
| `-q, --quality` | JPEG品質 | 85 |

### 例: トークン節約のため縮小

```bash
python compare_screenshots.py before.png after.png -s 0.5 -q 50
```

---

## 実践例

### 例1: PRレビューでのUI変更確認

```bash
# 変更前後のスクリーンショットを比較
python compare_screenshots.py \
  screenshots/main_before.png \
  screenshots/main_after.png \
  -o pr_review

# Claudeに確認を依頼
# "pr_review/diff_highlight.jpg を見て、UIの変更点を説明してください"
```

### 例2: 複数画面の回帰テスト

```bash
# 各画面を比較
python compare_screenshots.py baseline/home.png current/home.png -o diff/home
python compare_screenshots.py baseline/settings.png current/settings.png -o diff/settings
python compare_screenshots.py baseline/profile.png current/profile.png -o diff/profile

# まとめてClaudeに確認
# "diff/ 以下の画像を見て、意図しない変更がないか確認してください"
```

### 例3: バグ修正の検証

```bash
python compare_screenshots.py bug_before.png bug_after.png -o bug_fix

# Claudeに確認
# "bug_fix/diff_highlight.jpg を見て、バグが修正されているか確認してください。
#  修正前は〇〇が△△になっていました。"
```

---

## 類似度スコアの見方

| スコア | 判定 | 意味 |
|--------|------|------|
| 100% | ✓ 同一 | 完全に同じ画像 |
| 95-99% | △ ほぼ同じ | 軽微な差分（フォント、微小な位置ずれ等） |
| 80-94% | △ 一部変更あり | 明確な変更がある |
| 80%未満 | ✗ 大きく異なる | 大幅なレイアウト変更 |

---

## Claude Codeとの連携

### 差分の説明を依頼

```
diff_output/diff_highlight.jpg を見て、
変更前後で何が変わったか箇条書きで教えてください
```

### 回帰バグの確認

```
diff_output/diff_highlight.jpg を見てください。
この変更は意図したものですか？
変更前はボタンが青色でしたが、意図せず色が変わっていないか確認してください。
```

### 修正提案を依頼

```
diff_output/diff_side_by_side.jpg を見てください。
左が期待する表示、右が現在の表示です。
右の表示を左に合わせるための修正方法を教えてください。
```
