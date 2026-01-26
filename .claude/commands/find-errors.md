---
description: 動画/画像からエラーや異常画面を検出
---

# エラー/異常画面検出

対象ファイル: $ARGUMENTS

## 実行手順

動画ファイル(.mp4, .mov等)または画像ファイル(.png, .jpg等)を指定してください。

```bash
pip install -q opencv-python numpy Pillow
python .claude_skills/video/detect_anomaly_screens.py $ARGUMENTS -o anomalies -s 0.5
```

実行後、`anomalies/` 内の画像を確認して:
- 🔴 エラー画面（*_error.jpg）の内容
- 🟡 警告画面（*_warning.jpg）の内容
- 発生タイミングと原因の推測
- コスト情報

を報告してください。
