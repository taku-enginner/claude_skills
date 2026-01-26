# エラー/異常画面検出 使い方ガイド

動画やスクリーンショットからエラー画面や異常な画面を自動検出するツールです。

## 検出対象

| 異常タイプ | 検出方法 | 深刻度 |
|------------|----------|--------|
| 🔴 エラー表示 | 赤色の領域を検出 | error |
| 🔴 空白画面 | 単色（白/黒）画面を検出 | error |
| 🟡 警告表示 | 黄色/オレンジの領域を検出 | warning |
| 🔵 ダイアログ | 中央の矩形領域を検出 | info |
| 🔵 ローディング | 円形インジケータを検出 | info |

---

## 基本的な使い方

### 動画から検出

```bash
python detect_anomaly_screens.py test_recording.mp4
```

### 画像から検出

```bash
python detect_anomaly_screens.py screenshot1.png screenshot2.png screenshot3.png
```

---

## 出力例

```
動画を分析中: test_recording.mp4
  フレーム数: 300, FPS: 30.00
  サンプリング間隔: 10フレームごと

==================================================
分析完了!
==================================================

分析対象: test_recording.mp4
分析フレーム数: 30
異常検出数: 5件

深刻度別:
  🔴 error: 2件
  🟡 warning: 1件
  🔵 info: 2件

検出された異常画面:
  🔴 [0:02.33] エラー表示（赤）
     → anomaly_output/anomaly_000070_error.jpg
  🔴 [0:03.00] 空白画面
     → anomaly_output/anomaly_000090_error.jpg
  🟡 [0:05.67] 警告表示
     → anomaly_output/anomaly_000170_warning.jpg
  🔵 [0:07.00] ダイアログ/ポップアップ
     → anomaly_output/anomaly_000210_info.jpg
  🔵 [0:08.33] ローディング
     → anomaly_output/anomaly_000250_info.jpg

出力ディレクトリ: anomaly_output
```

---

## オプション

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ディレクトリ | anomaly_output |
| `-i, --interval` | サンプリング間隔（動画のみ） | 10 |
| `-s, --scale` | 出力画像のスケール | 0.5 |
| `-q, --quality` | JPEG品質 | 50 |

### サンプリング間隔について

- 値が小さいほど細かくチェック（時間がかかる）
- 値が大きいほど粗くチェック（見逃す可能性）

| 値 | 用途 |
|----|------|
| 5 | 短い動画、エラーを見逃したくない場合 |
| 10 | 一般的な用途（推奨） |
| 30 | 長い動画、概要把握 |

---

## 実践例

### 例1: E2Eテスト録画の確認

```bash
# テスト実行時の画面録画を分析
python detect_anomaly_screens.py e2e_test_recording.mp4 -o e2e_anomalies -i 5

# エラーがあればClaudeに確認
# "e2e_anomalies/ の画像を見て、何が起きているか説明してください"
```

### 例2: 手動テストの録画確認

```bash
# 長めの手動テスト録画を分析
python detect_anomaly_screens.py manual_test.mp4 -o manual_anomalies -i 30

# 検出された異常をClaudeに確認
```

### 例3: スクリーンショット一括チェック

```bash
# テスト結果のスクリーンショットをまとめてチェック
python detect_anomaly_screens.py test_results/*.png -o anomaly_check
```

### 例4: CI/CDでの自動チェック

```bash
# CIで異常画面が検出されたらエラー
python detect_anomaly_screens.py test_recording.mp4 -o ci_anomalies

# 出力ディレクトリにerrorファイルがあれば失敗
if ls ci_anomalies/*_error.jpg 1> /dev/null 2>&1; then
    echo "エラー画面が検出されました"
    exit 1
fi
```

---

## 検出精度を上げるコツ

### エラー画面が検出されない場合

アプリのエラー表示が赤以外の場合は検出されません。
その場合は、キーフレーム抽出（`extract_keyframes.py`）で全体を抽出し、
Claudeに確認を依頼してください。

```bash
# キーフレームを抽出
python extract_keyframes.py video.mp4 -t 0.90

# Claudeに確認
# "keyframes/ の画像を見て、エラーや異常な画面がないか確認してください"
```

### 誤検出が多い場合

赤いUIが多いアプリでは誤検出が増えます。
その場合は、出力された画像をClaudeに確認してもらい、
本当のエラーかどうか判断してもらいましょう。

---

## Claude Codeとの連携

### 異常の原因を調査

```
anomaly_output/anomaly_000070_error.jpg を見てください。
このエラー画面の原因として考えられることを教えてください。
```

### バグの再現手順を推測

```
anomaly_output/ にある全ての画像を時系列で見てください。
このエラーが発生するまでの操作手順を推測してください。
```

### 修正方法を提案

```
anomaly_output/anomaly_000090_error.jpg を見てください。
この空白画面が表示される原因と修正方法を提案してください。
関連しそうなコードは src/screens/ にあります。
```

---

## よくある質問

### Q: ローディング画面を無視したい

現在は検出されますが、深刻度は `info` なので、
`error` と `warning` のファイルだけを確認すればOKです。

```bash
# errorとwarningのみ確認
ls anomaly_output/*_error.jpg anomaly_output/*_warning.jpg
```

### Q: 特定の色のエラーを検出したい

現在のスクリプトは赤色に特化しています。
別の色を検出したい場合は、スクリプトの `AnomalyDetector` クラスの
HSV範囲を調整してください。

### Q: 動画が長すぎて時間がかかる

サンプリング間隔を大きくしてください。

```bash
python detect_anomaly_screens.py long_video.mp4 -i 60  # 60フレームごと
```
