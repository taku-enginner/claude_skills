---
name: flutter-run
description: Flutter開発時のホットリロード自動化。実装作業完了後に自動で呼び出される。Dart変更はhot reload、ネイティブ/設定変更はhot restartを実行。
---

# Flutter Hot Reload スキル

実装作業完了後にFlutterアプリを自動的にiOSデバイスで実行/リロードします。

## 自動呼び出しルール

**Claudeは以下の作業完了後、必ずこのスキルを呼び出してください:**

- `lib/**/*.dart` ファイルの編集完了後
- `test/**/*.dart` ファイルの編集完了後
- `pubspec.yaml` の変更後
- `ios/` または `android/` 配下のファイル変更後
- `assets/` 配下のファイル変更後

## コマンド

```bash
# 基本コマンド
.claude/scripts/flutter-run.sh start    # 新規起動
.claude/scripts/flutter-run.sh reload   # Hot Reload (r)
.claude/scripts/flutter-run.sh restart  # Hot Restart (R)
.claude/scripts/flutter-run.sh status   # 状態確認
.claude/scripts/flutter-run.sh stop     # 停止
```

## 判断ロジック

### Hot Reload を使う場合（高速）
- Dartファイルのみの変更 (`lib/**/*.dart`, `test/**/*.dart`)

### Hot Restart を使う場合（状態リセット）
- `pubspec.yaml` / `pubspec.lock` の変更
- `ios/**/*` / `android/**/*` の変更
- `assets/**/*` の変更
- `.env` の変更

### 新規起動が必要な場合
- flutter runが実行されていない場合
- ネイティブコードの大きな変更（ビルドが必要）

## 使用例

```
# 実装完了後の呼び出し例

# Dartファイルのみ変更した場合
.claude/scripts/flutter-run.sh reload

# pubspec.yamlを変更した場合
.claude/scripts/flutter-run.sh restart

# 初回起動または停止後
.claude/scripts/flutter-run.sh start
```

## セッション管理

ログを確認したい場合:
```bash
tmux attach -t flutter_run
# デタッチ: Ctrl+B, D
```

## トラブルシューティング

### デバイスが見つからない
```bash
flutter devices
```

### セッションの強制終了
```bash
tmux kill-session -t flutter_run
```

### ビルドエラー
```bash
flutter clean && flutter pub get
.claude/scripts/flutter-run.sh start
```
