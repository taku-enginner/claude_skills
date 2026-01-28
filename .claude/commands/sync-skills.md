# スキル同期コマンド

プロジェクト固有のスキルをclaude_skillsディレクトリに同期します。

## 使い方

```bash
.claude/scripts/sync-skills.sh [プロジェクトディレクトリ]
```

## 動作

1. プロジェクトの `.claude.backup` または非シンボリックリンクの `.claude` を検出
2. 以下のディレクトリを比較:
   - `skills/` - スキル定義
   - `scripts/` - シェルスクリプト
   - `commands/` - スラッシュコマンド
3. 差分を表示し、確認後に同期を実行

## 実行

現在のプロジェクトで同期を実行:

```bash
.claude/scripts/sync-skills.sh
```

## 注意

- 同期先: `/Users/taku/myapp/claude_skills/.claude/`
- 既存ファイルは上書きされます
- 同期前に差分を確認できます
