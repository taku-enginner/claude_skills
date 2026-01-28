#!/bin/bash

# ===========================================
# プロジェクト固有スキルをclaude_skillsに同期
# ===========================================

set -e

CLAUDE_SKILLS_DIR="/Users/taku/myapp/claude_skills"
PROJECT_DIR="${1:-.}"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "スキル同期ツール"
echo -e "==========================================${NC}"
echo ""

# プロジェクトディレクトリの確認
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}エラー: ディレクトリが見つかりません: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"
PROJECT_DIR=$(pwd)
echo -e "プロジェクト: ${GREEN}$PROJECT_DIR${NC}"
echo ""

# 同期元の検出（.claude.backup または .claude がシンボリックリンクでない場合）
SYNC_SOURCE=""
if [ -d ".claude.backup" ]; then
    SYNC_SOURCE=".claude.backup"
    echo -e "同期元: ${GREEN}.claude.backup${NC}"
elif [ -d ".claude" ] && [ ! -L ".claude" ]; then
    SYNC_SOURCE=".claude"
    echo -e "同期元: ${GREEN}.claude${NC}"
else
    echo -e "${YELLOW}同期元が見つかりません（.claude.backup または非シンボリックリンクの.claude）${NC}"
    echo "このプロジェクトは既にclaude_skillsにリンクされている可能性があります。"
    exit 0
fi

echo ""
echo -e "${BLUE}--- スキルの差分チェック ---${NC}"
echo ""

# スキルの差分チェック
SKILLS_SYNCED=0
SKILLS_NEW=0
SKILLS_UPDATED=0

# skills ディレクトリの同期
if [ -d "$SYNC_SOURCE/skills" ]; then
    for skill_dir in "$SYNC_SOURCE/skills"/*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            target_dir="$CLAUDE_SKILLS_DIR/.claude/skills/$skill_name"

            if [ ! -d "$target_dir" ]; then
                echo -e "${GREEN}[新規] skills/$skill_name${NC}"
                ((SKILLS_NEW++))
            else
                # 差分チェック
                diff_result=$(diff -rq "$skill_dir" "$target_dir" 2>/dev/null || true)
                if [ -n "$diff_result" ]; then
                    echo -e "${YELLOW}[更新] skills/$skill_name${NC}"
                    echo "$diff_result" | head -5
                    ((SKILLS_UPDATED++))
                else
                    echo -e "[同期済] skills/$skill_name"
                    ((SKILLS_SYNCED++))
                fi
            fi
        fi
    done
fi

# scripts ディレクトリの同期
if [ -d "$SYNC_SOURCE/scripts" ]; then
    for script_file in "$SYNC_SOURCE/scripts"/*; do
        if [ -f "$script_file" ]; then
            script_name=$(basename "$script_file")
            target_file="$CLAUDE_SKILLS_DIR/.claude/scripts/$script_name"

            if [ ! -f "$target_file" ]; then
                echo -e "${GREEN}[新規] scripts/$script_name${NC}"
                ((SKILLS_NEW++))
            else
                if ! diff -q "$script_file" "$target_file" > /dev/null 2>&1; then
                    echo -e "${YELLOW}[更新] scripts/$script_name${NC}"
                    ((SKILLS_UPDATED++))
                else
                    echo -e "[同期済] scripts/$script_name"
                    ((SKILLS_SYNCED++))
                fi
            fi
        fi
    done
fi

# commands ディレクトリの同期
if [ -d "$SYNC_SOURCE/commands" ]; then
    for cmd_file in "$SYNC_SOURCE/commands"/*; do
        if [ -f "$cmd_file" ]; then
            cmd_name=$(basename "$cmd_file")
            target_file="$CLAUDE_SKILLS_DIR/.claude/commands/$cmd_name"

            if [ ! -f "$target_file" ]; then
                echo -e "${GREEN}[新規] commands/$cmd_name${NC}"
                ((SKILLS_NEW++))
            else
                if ! diff -q "$cmd_file" "$target_file" > /dev/null 2>&1; then
                    echo -e "${YELLOW}[更新] commands/$cmd_name${NC}"
                    ((SKILLS_UPDATED++))
                else
                    echo -e "[同期済] commands/$cmd_name"
                    ((SKILLS_SYNCED++))
                fi
            fi
        fi
    done
fi

echo ""
echo -e "${BLUE}--- サマリー ---${NC}"
echo "同期済: $SKILLS_SYNCED"
echo "新規: $SKILLS_NEW"
echo "更新: $SKILLS_UPDATED"
echo ""

# 同期の実行確認
if [ $SKILLS_NEW -eq 0 ] && [ $SKILLS_UPDATED -eq 0 ]; then
    echo -e "${GREEN}すべてのスキルは同期済みです。${NC}"
    exit 0
fi

echo -e "${YELLOW}上記のスキルをclaude_skillsに同期しますか？ [y/N]${NC}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "同期をキャンセルしました。"
    exit 0
fi

echo ""
echo -e "${BLUE}--- 同期実行中 ---${NC}"

# skills の同期
if [ -d "$SYNC_SOURCE/skills" ]; then
    for skill_dir in "$SYNC_SOURCE/skills"/*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            target_dir="$CLAUDE_SKILLS_DIR/.claude/skills/$skill_name"

            if [ ! -d "$target_dir" ] || ! diff -rq "$skill_dir" "$target_dir" > /dev/null 2>&1; then
                mkdir -p "$target_dir"
                cp -R "$skill_dir"/* "$target_dir/"
                echo -e "${GREEN}✓ skills/$skill_name を同期しました${NC}"
            fi
        fi
    done
fi

# scripts の同期
if [ -d "$SYNC_SOURCE/scripts" ]; then
    for script_file in "$SYNC_SOURCE/scripts"/*; do
        if [ -f "$script_file" ]; then
            script_name=$(basename "$script_file")
            target_file="$CLAUDE_SKILLS_DIR/.claude/scripts/$script_name"

            if [ ! -f "$target_file" ] || ! diff -q "$script_file" "$target_file" > /dev/null 2>&1; then
                cp "$script_file" "$target_file"
                chmod +x "$target_file"
                echo -e "${GREEN}✓ scripts/$script_name を同期しました${NC}"
            fi
        fi
    done
fi

# commands の同期
if [ -d "$SYNC_SOURCE/commands" ]; then
    mkdir -p "$CLAUDE_SKILLS_DIR/.claude/commands"
    for cmd_file in "$SYNC_SOURCE/commands"/*; do
        if [ -f "$cmd_file" ]; then
            cmd_name=$(basename "$cmd_file")
            target_file="$CLAUDE_SKILLS_DIR/.claude/commands/$cmd_name"

            if [ ! -f "$target_file" ] || ! diff -q "$cmd_file" "$target_file" > /dev/null 2>&1; then
                cp "$cmd_file" "$target_file"
                echo -e "${GREEN}✓ commands/$cmd_name を同期しました${NC}"
            fi
        fi
    done
fi

echo ""
echo -e "${GREEN}=========================================="
echo "同期完了！"
echo -e "==========================================${NC}"
