#!/bin/bash
#
# Claude Skills セットアップスクリプト
#
# 使い方:
#   ./setup.sh /path/to/your/project
#
# これにより、プロジェクトで以下が使えるようになります:
#   - CLAUDE.md による自然言語でのスキル呼び出し
#   - /project:analyze-video などのスラッシュコマンド
#

set -e

# 引数チェック
if [ -z "$1" ]; then
    echo "使い方: $0 <プロジェクトディレクトリ>"
    echo ""
    echo "例:"
    echo "  $0 /path/to/my-app"
    echo "  $0 ."
    exit 1
fi

PROJECT_DIR=$(realpath "$1")
SKILLS_DIR=$(dirname "$(realpath "$0")")

echo "Claude Skills セットアップ"
echo "=========================="
echo "スキルディレクトリ: $SKILLS_DIR"
echo "プロジェクト: $PROJECT_DIR"
echo ""

# プロジェクトディレクトリの存在確認
if [ ! -d "$PROJECT_DIR" ]; then
    echo "エラー: プロジェクトディレクトリが存在しません: $PROJECT_DIR"
    exit 1
fi

# 既存のCLAUDE.mdをバックアップ
if [ -f "$PROJECT_DIR/CLAUDE.md" ] && [ ! -L "$PROJECT_DIR/CLAUDE.md" ]; then
    echo "既存のCLAUDE.mdをバックアップ: CLAUDE.md.backup"
    mv "$PROJECT_DIR/CLAUDE.md" "$PROJECT_DIR/CLAUDE.md.backup"
fi

# シンボリックリンクを作成
echo "シンボリックリンクを作成中..."

# CLAUDE.md
ln -sf "$SKILLS_DIR/CLAUDE.md" "$PROJECT_DIR/CLAUDE.md"
echo "  ✓ CLAUDE.md"

# .claude ディレクトリ（コマンド用）
if [ -d "$PROJECT_DIR/.claude" ] && [ ! -L "$PROJECT_DIR/.claude" ]; then
    echo "  既存の .claude ディレクトリを .claude.backup に移動"
    mv "$PROJECT_DIR/.claude" "$PROJECT_DIR/.claude.backup"
fi
ln -sf "$SKILLS_DIR/.claude" "$PROJECT_DIR/.claude"
echo "  ✓ .claude/"

# スキルディレクトリ
ln -sf "$SKILLS_DIR/skills" "$PROJECT_DIR/.claude_skills"
echo "  ✓ .claude_skills/ -> skills/"

echo ""
echo "セットアップ完了!"
echo ""
echo "使い方:"
echo "  Claude Codeで以下のように話しかけてください:"
echo "    「テスト動画を確認して」"
echo "    「スクショを比較して」"
echo "    「エラーを探して」"
echo ""
echo "  またはスラッシュコマンド:"
echo "    /project:analyze-video video.mp4"
echo "    /project:compare-screens before.png after.png"
echo "    /project:find-errors video.mp4"
echo ""
echo "依存パッケージのインストール:"
echo "  pip install -r $SKILLS_DIR/requirements.txt"
