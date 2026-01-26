# Claude Code スキル設定

このリポジトリには、スマホアプリのテスト効率化のためのスキルが含まれています。

## セットアップ

他のプロジェクトでこのスキルを使う場合:

```bash
/path/to/claude_skills/setup.sh /path/to/your/project
```

## 利用可能なスキル

### 1. 動画/テスト動画の確認を依頼されたら

ユーザーが「動画を確認して」「テスト動画を見て」「録画をチェックして」などと言ったら、以下を実行:

```bash
# まず依存パッケージを確認
pip install -q opencv-python numpy Pillow

# キーフレームを抽出（コスト削減）
python .claude_skills/video/extract_keyframes.py <動画パス> -o keyframes -t 0.85 -q 30 -s 0.3

# 異常画面を検出
python .claude_skills/video/detect_anomaly_screens.py <動画パス> -o anomalies
```

その後、`keyframes/` と `anomalies/` の画像を読み込んで内容を確認する。

### 2. スクリーンショットの比較を依頼されたら

ユーザーが「スクショを比較して」「画面の差分を見て」「変更前後を確認して」などと言ったら:

```bash
python .claude_skills/video/compare_screenshots.py <画像1> <画像2> -o diff_output
```

その後、`diff_output/diff_highlight.jpg` を読み込んで差分を説明する。

### 3. エラー画面/異常を探してと言われたら

ユーザーが「エラーを探して」「異常がないか確認して」「問題のある画面を見つけて」などと言ったら:

```bash
python .claude_skills/video/detect_anomaly_screens.py <動画または画像> -o anomalies
```

その後、`anomalies/` 内の画像を確認し、検出された問題を報告する。

## スキルの使い分け

| ユーザーの依頼 | 使うスキル |
|----------------|------------|
| 動画を見て/確認して | extract_keyframes.py → 画像を読む |
| テスト動画をチェック | extract_keyframes.py + detect_anomaly_screens.py |
| スクショを比較 | compare_screenshots.py |
| エラーを探して | detect_anomaly_screens.py |
| バグの原因を調べて | extract_keyframes.py → 画像を読んで分析 |
| 画面遷移を確認 | extract_keyframes.py -t 0.80 → 画像を読む |

## 実行後の確認

スクリプト実行後は、必ず出力された画像を `Read` ツールで読み込んで内容を確認すること。
画像を見ずに回答しないこと。

## 結果報告のフォーマット

スキル実行後は、以下の形式で結果を報告すること:

```
## 分析結果

### 検出内容
- [検出された内容を箇条書き]

### 使用コスト
- 画像数: X枚
- トークン数: 約X,XXXトークン
- 料金: $X.XXXX (約XX円)

### 詳細
[画像を見て分析した詳細]
```

コスト情報はスクリプトの出力に含まれているので、それを報告に含めること。

## オプションの目安

### extract_keyframes.py
- `-t 0.95`: 細かい変化も検出（アニメーション確認）
- `-t 0.85`: 標準（推奨）
- `-t 0.70`: 大きな変化のみ（長い動画）

### detect_anomaly_screens.py
- `-i 5`: 細かくチェック（短い動画）
- `-i 10`: 標準（推奨）
- `-i 30`: 粗くチェック（長い動画）

### compare_screenshots.py
- `-s 0.5`: トークン節約
- `-s 1.0`: 詳細確認

## スキル一覧

| カテゴリ | スキル | 説明 |
|----------|--------|------|
| video | extract_keyframes.py | 動画からキーフレーム抽出 |
| video | compare_screenshots.py | スクショ差分比較 |
| video | detect_anomaly_screens.py | エラー/異常画面検出 |
