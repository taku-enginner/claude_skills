# Claude Code スキル設定

このリポジトリには、スマホアプリのテスト効率化のためのスキルが含まれています。

## セットアップ

他のプロジェクトでこのスキルを使う場合:

```bash
/path/to/claude_skills/setup.sh /path/to/your/project
```

---

## 🔥 Flutter実装フロー（重要）

**ユーザーが「〇〇を実装して」と言ったら、以下のフローを自動で実行すること:**

### フロー

```
1. 実装
     ↓
2. テストケース生成
     ↓
3. テスト実行
     ↓
4. 失敗? ──Yes──→ 実装を修正して3へ（最大3回）
     │
     No
     ↓
5. 完了報告
```

### 具体的な手順

#### Step 1: 実装
- ユーザーの要求に基づいてDartコードを実装

#### Step 2: テストケース生成
```bash
python .claude_skills/code/generate_tests.py <実装したファイル> --force
```

#### Step 3: テスト実行
```bash
python .claude_skills/code/run_tests.py <テストファイル>
```

#### Step 4: 失敗時の対応
- **1-3回目の失敗**: エラー内容を確認し、実装を修正して再テスト
- **3回失敗**: ユーザーに相談（下記フォーマット）

### 3回失敗時の相談フォーマット

```
## テストが3回失敗しました

### 失敗しているテスト
- [テスト名]: [エラー内容]

### 試した修正
1. [1回目の修正内容]
2. [2回目の修正内容]
3. [3回目の修正内容]

### 考えられる原因
- [原因1]
- [原因2]

### 質問
[具体的な質問や確認事項]

どのように対応しますか？
```

### 完了報告フォーマット

```
## 実装完了

### 実装内容
- [実装した機能の説明]

### 作成/変更したファイル
- lib/xxx.dart (新規作成)
- test/xxx_test.dart (新規作成)

### テスト結果
- 合計: X件
- 成功: X件 ✅
- 失敗: 0件

### 次のステップ
[必要に応じて]
```

---

## 利用可能なスキル

### 動画/画像スキル

#### 1. 動画/テスト動画の確認を依頼されたら

ユーザーが「動画を確認して」「テスト動画を見て」「録画をチェックして」などと言ったら、以下を実行:

```bash
pip install -q opencv-python numpy Pillow
python .claude_skills/video/extract_keyframes.py <動画パス> -o keyframes -t 0.85 -q 30 -s 0.3
python .claude_skills/video/detect_anomaly_screens.py <動画パス> -o anomalies
```

その後、`keyframes/` と `anomalies/` の画像を読み込んで内容を確認する。

#### 2. スクリーンショットの比較を依頼されたら

ユーザーが「スクショを比較して」「画面の差分を見て」「変更前後を確認して」などと言ったら:

```bash
python .claude_skills/video/compare_screenshots.py <画像1> <画像2> -o diff_output
```

その後、`diff_output/diff_highlight.jpg` を読み込んで差分を説明する。

#### 3. エラー画面/異常を探してと言われたら

ユーザーが「エラーを探して」「異常がないか確認して」「問題のある画面を見つけて」などと言ったら:

```bash
python .claude_skills/video/detect_anomaly_screens.py <動画または画像> -o anomalies
```

その後、`anomalies/` 内の画像を確認し、検出された問題を報告する。

### コードスキル（Flutter）

#### 4. Dartコードを解析したい時

```bash
python .claude_skills/code/analyze_dart.py <dartファイル>
python .claude_skills/code/analyze_dart.py lib/ --recursive
```

#### 5. テストを生成したい時

```bash
python .claude_skills/code/generate_tests.py <dartファイル>
python .claude_skills/code/generate_tests.py lib/utils/validator.dart --dry-run
```

#### 6. テストを実行したい時

```bash
python .claude_skills/code/run_tests.py
python .claude_skills/code/run_tests.py test/utils/validator_test.dart
python .claude_skills/code/run_tests.py --coverage
```

---

## スキルの使い分け

| ユーザーの依頼 | 使うスキル |
|----------------|------------|
| 〇〇を実装して | 実装 → generate_tests → run_tests（自動フロー） |
| テストを書いて | generate_tests.py |
| テストを実行して | run_tests.py |
| コードを解析して | analyze_dart.py |
| 動画を見て/確認して | extract_keyframes.py → 画像を読む |
| テスト動画をチェック | extract_keyframes.py + detect_anomaly_screens.py |
| スクショを比較 | compare_screenshots.py |
| エラーを探して | detect_anomaly_screens.py |

---

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

---

## スキル一覧

| カテゴリ | スキル | 説明 |
|----------|--------|------|
| video | extract_keyframes.py | 動画からキーフレーム抽出 |
| video | compare_screenshots.py | スクショ差分比較 |
| video | detect_anomaly_screens.py | エラー/異常画面検出 |
| code | analyze_dart.py | Dartコード解析 |
| code | generate_tests.py | Flutterテスト生成 |
| code | run_tests.py | テスト実行・レポート |
