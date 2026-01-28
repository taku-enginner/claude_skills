#!/bin/bash
#
# Flutter Run / Hot Reload スクリプト
#
# 使用方法:
#   .claude/scripts/flutter-run.sh start    # 新規起動
#   .claude/scripts/flutter-run.sh reload   # Hot Reload (r)
#   .claude/scripts/flutter-run.sh restart  # Hot Restart (R)
#   .claude/scripts/flutter-run.sh status   # ステータス確認
#   .claude/scripts/flutter-run.sh stop     # 停止
#

set -e

# スクリプトのディレクトリからプロジェクトルートを特定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 定数
SESSION_NAME="flutter_run"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$PROJECT_DIR"

# iOSデバイスIDを取得
get_ios_device_id() {
    flutter devices 2>/dev/null | grep -i "ios" | grep -v "simulator" | head -1 | awk -F'•' '{print $2}' | xargs
}

# tmuxセッションが存在するか確認
session_exists() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

# 新規起動
start_flutter() {
    if session_exists; then
        echo -e "${YELLOW}⚠️  セッション '$SESSION_NAME' は既に存在します${NC}"
        echo "   停止するには: $0 stop"
        echo "   ステータス確認: $0 status"
        echo ""
        echo -e "${BLUE}ヒント: Hot Reload/Restart を送信しますか？${NC}"
        echo "   .claude/scripts/flutter-run.sh reload"
        echo "   .claude/scripts/flutter-run.sh restart"
        exit 1
    fi

    local device_id=$(get_ios_device_id)

    if [ -z "$device_id" ]; then
        echo -e "${RED}❌ iOSデバイスが見つかりません${NC}"
        echo ""
        echo "接続されているデバイスを確認:"
        flutter devices
        exit 1
    fi

    echo -e "${GREEN}🚀 Flutter を起動中...${NC}"
    echo "   プロジェクト: $PROJECT_DIR"
    echo "   デバイス: $device_id"
    echo ""

    # tmuxセッションを作成してflutter runを実行
    tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR" "flutter run -d '$device_id'; echo ''; echo 'Flutter が終了しました。何かキーを押すとセッションを終了します...'; read"

    echo -e "${GREEN}✅ Flutter を起動しました${NC}"
    echo ""
    echo "   セッション接続: tmux attach -t $SESSION_NAME"
    echo "   デタッチ: Ctrl+B, D"
    echo ""
    echo -e "${BLUE}📱 初回ビルドには時間がかかります。しばらくお待ちください...${NC}"
}

# Hot Reload を送信
send_reload() {
    if ! session_exists; then
        echo -e "${YELLOW}⚠️  セッションが存在しません。起動します...${NC}"
        start_flutter
        return
    fi

    echo -e "${GREEN}🔄 Hot Reload を送信中...${NC}"
    tmux send-keys -t "$SESSION_NAME" "r"
    echo -e "${GREEN}✅ Hot Reload を送信しました${NC}"
}

# Hot Restart を送信
send_restart() {
    if ! session_exists; then
        echo -e "${YELLOW}⚠️  セッションが存在しません。起動します...${NC}"
        start_flutter
        return
    fi

    echo -e "${GREEN}🔄 Hot Restart を送信中...${NC}"
    tmux send-keys -t "$SESSION_NAME" "R"
    echo -e "${GREEN}✅ Hot Restart を送信しました${NC}"
}

# ステータス確認
check_status() {
    echo "=========================================="
    echo "Flutter Run ステータス"
    echo "=========================================="

    if session_exists; then
        echo -e "${GREEN}✅ セッション '$SESSION_NAME' は実行中です${NC}"
        echo ""
        echo "セッション接続: tmux attach -t $SESSION_NAME"
        echo ""
        echo "最近の出力:"
        echo "----------"
        tmux capture-pane -t "$SESSION_NAME" -p | tail -10
    else
        echo -e "${YELLOW}⚠️  セッション '$SESSION_NAME' は存在しません${NC}"
        echo ""
        echo "起動: $0 start"
    fi
}

# 停止
stop_flutter() {
    if ! session_exists; then
        echo -e "${YELLOW}⚠️  セッション '$SESSION_NAME' は存在しません${NC}"
        return
    fi

    echo -e "${YELLOW}🛑 Flutter を停止中...${NC}"

    # qを送信してflutter runを終了
    tmux send-keys -t "$SESSION_NAME" "q"
    sleep 2

    # セッションを終了
    if session_exists; then
        tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ 停止しました${NC}"
}

# ヘルプ表示
show_help() {
    echo "Flutter Run / Hot Reload スクリプト"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "コマンド:"
    echo "  start     flutter run を新規起動"
    echo "  reload    Hot Reload (r) を送信"
    echo "  restart   Hot Restart (R) を送信"
    echo "  status    実行状態を確認"
    echo "  stop      停止"
    echo "  help      このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 start     # アプリを起動"
    echo "  $0 reload    # Dart変更後にリロード"
    echo "  $0 restart   # 設定変更後にリスタート"
}

# メイン処理
case "${1:-help}" in
    start)
        start_flutter
        ;;
    reload)
        send_reload
        ;;
    restart)
        send_restart
        ;;
    status)
        check_status
        ;;
    stop)
        stop_flutter
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 不明なコマンド: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
