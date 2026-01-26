# Claude Code Skills

スマホアプリのテスト効率化のためのスキル集です。
Claude Codeに自然言語で話しかけるだけで、各種スキルが自動で実行されます。

---

## スキル一覧

### 動画/画像スキル

| スキル | 説明 | 使用例 |
|--------|------|--------|
| **キーフレーム抽出** | 動画からキーフレームを抽出し、コストを約1/19に削減 | 「テスト動画を確認して」 |
| **スクリーンショット比較** | 2つの画像の差分をハイライト表示 | 「スクショを比較して」 |
| **エラー画面検出** | エラー・警告・異常画面を自動検出 | 「エラーを探して」 |

### コードスキル（Flutter）

| スキル | 説明 | 使用例 |
|--------|------|--------|
| **Dart解析** | 関数・クラス構造を解析 | 「このファイルの構造を教えて」 |
| **テスト生成** | Dartコードからテストを自動生成 | 「テストを書いて」 |
| **テスト実行** | flutter testを実行しレポート生成 | 「テストを実行して」 |

---

## クイックスタート

### 1. クローン

```bash
git clone https://github.com/your-repo/claude_skills.git
cd claude_skills
```

### 2. 依存パッケージをインストール

```bash
pip install opencv-python numpy Pillow
```

### 3. 他のプロジェクトで使う場合

```bash
./setup.sh /path/to/your/project
```

これにより、対象プロジェクトにシンボリックリンクが作成され、Claude Codeがスキルを認識します。

---

## 自然言語で使う

Claude Codeを起動して、普通に話しかけるだけ:

```
あなた: テスト動画を確認して
        recordings/test.mp4

Claude: 動画を解析します...
        [キーフレーム抽出・異常検出を実行]
        [結果を報告]
```

```
あなた: メールバリデーション関数を実装して

Claude: 実装します...
        [コード作成 → テスト生成 → テスト実行]
        [完了報告]
```

詳しい例は [docs/usage_natural_language.md](docs/usage_natural_language.md) を参照。

---

## スキル詳細

### キーフレーム抽出

動画をClaude Codeに安く渡すためのスキル。

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| フレーム数 | 71枚 | 52枚 |
| サイズ | 443×960 | 266×576 px |
| コスト | 約450円 | **約24円** |

```bash
python skills/video/extract_keyframes.py video.mp4 -o keyframes -t 0.85 -q 30 -s 0.3
```

詳細: [docs/video/usage_extract_keyframes.md](docs/video/usage_extract_keyframes.md)

---

### スクリーンショット比較

2つの画像の差分をマゼンタでハイライト表示。

```bash
python skills/video/compare_screenshots.py before.png after.png -o diff_output
```

詳細: [docs/video/usage_compare_screenshots.md](docs/video/usage_compare_screenshots.md)

---

### エラー画面検出

動画や画像からエラー・警告・異常画面を自動検出。

検出対象:
- 赤いエラーメッセージ
- 黄色い警告
- 空白/真っ白な画面
- ダイアログ/ポップアップ
- ローディング画面

```bash
python skills/video/detect_anomaly_screens.py video.mp4 -o anomalies
```

詳細: [docs/video/usage_detect_anomaly_screens.md](docs/video/usage_detect_anomaly_screens.md)

---

### Flutter テスト自動化

「〇〇を実装して」と指示するだけで:

1. 機能を実装
2. テストを自動生成
3. テストを実行
4. 失敗したら修正して再テスト（最大3回）
5. 完了報告

```
実装 → テスト生成 → テスト実行 → 失敗? → 修正 → 再テスト → 完了
```

詳細: [docs/code/usage_flutter_test.md](docs/code/usage_flutter_test.md)

---

## ディレクトリ構成

```
claude_skills/
├── README.md              # このファイル
├── CLAUDE.md              # Claude Code用ルール定義
├── setup.sh               # 他プロジェクトへのリンクスクリプト
├── skills/
│   ├── video/
│   │   ├── extract_keyframes.py
│   │   ├── compare_screenshots.py
│   │   └── detect_anomaly_screens.py
│   └── code/
│       ├── analyze_dart.py
│       ├── generate_tests.py
│       └── run_tests.py
├── docs/
│   ├── usage_natural_language.md   # 自然言語使用例
│   ├── video/
│   │   ├── usage_extract_keyframes.md
│   │   ├── usage_compare_screenshots.md
│   │   └── usage_detect_anomaly_screens.md
│   └── code/
│       └── usage_flutter_test.md
└── .claude/
    └── commands/          # スラッシュコマンド定義
```

---

## ドキュメント

| ドキュメント | 内容 |
|--------------|------|
| [自然言語使用例](docs/usage_natural_language.md) | Claudeへの指示例 |
| [キーフレーム抽出](docs/video/usage_extract_keyframes.md) | 動画処理の詳細 |
| [スクショ比較](docs/video/usage_compare_screenshots.md) | 差分検出の詳細 |
| [エラー検出](docs/video/usage_detect_anomaly_screens.md) | 異常検出の詳細 |
| [Flutterテスト](docs/code/usage_flutter_test.md) | テスト自動化の詳細 |

---

## ライセンス

MIT License
