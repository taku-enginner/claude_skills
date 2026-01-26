---
description: テスト動画を分析してエラーや異常を検出
---

# 動画分析

動画ファイル: $ARGUMENTS

## 実行手順

1. 依存パッケージをインストール
2. キーフレームを抽出してトークンコストを削減
3. 異常画面（エラー、警告、空白画面など）を検出
4. 抽出した画像を確認して結果を報告

```bash
pip install -q opencv-python numpy Pillow
python extract_keyframes.py "$ARGUMENTS" -o keyframes -t 0.85 -q 30 -s 0.3
python detect_anomaly_screens.py "$ARGUMENTS" -o anomalies -i 10
```

実行後、以下を確認:
- `anomalies/` 内のエラー画面（*_error.jpg）
- `anomalies/` 内の警告画面（*_warning.jpg）
- `keyframes/` 内の主要フレーム

画像を読み込んで、検出された問題と画面遷移の流れを報告してください。
