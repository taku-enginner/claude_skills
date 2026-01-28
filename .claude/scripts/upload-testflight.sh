#!/bin/bash
#
# iOS TestFlight アップロードスクリプト（汎用版）
#
# 使用方法:
#   cd /path/to/your/flutter/project
#   .claude/scripts/upload-testflight.sh
#
# 使用前に以下の環境変数を設定してください:
#   export APPLE_ID="your@email.com"
#   export APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
#   export TEAM_ID="XXXXXXXXXX"              # 複数チームに所属している場合
#   export NTFY_TOPIC="your-unique-topic"    # Push通知用（任意）
#
set -e

# スクリプトのディレクトリからプロジェクトルートを特定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# pubspec.yaml の存在確認
if [ ! -f "$PROJECT_DIR/pubspec.yaml" ]; then
    echo "❌ エラー: pubspec.yaml が見つかりません"
    echo "   Flutter プロジェクトのルートから実行してください"
    exit 1
fi

cd "$PROJECT_DIR"

# アプリ名を pubspec.yaml から取得
APP_NAME=$(grep "^name:" pubspec.yaml | sed 's/name: //' | tr -d ' ')

# Push通知を送信する関数
send_notification() {
    local title="$1"
    local message="$2"
    local priority="${3:-default}"

    if [ -n "$NTFY_TOPIC" ]; then
        curl -s \
            -H "Title: $title" \
            -H "Priority: $priority" \
            -H "Tags: iphone,rocket" \
            -d "$message" \
            "https://ntfy.sh/$NTFY_TOPIC" > /dev/null 2>&1 || true
    fi
}

echo "=========================================="
echo "iOS TestFlight リリース自動化"
echo "アプリ: $APP_NAME"
echo "=========================================="

# 環境変数チェック
if [ -z "$APPLE_ID" ]; then
    echo "❌ エラー: APPLE_ID が設定されていません"
    echo "   export APPLE_ID=\"your@email.com\""
    exit 1
fi

if [ -z "$APP_SPECIFIC_PASSWORD" ]; then
    echo "❌ エラー: APP_SPECIFIC_PASSWORD が設定されていません"
    echo "   Apple ID > サインインとセキュリティ > App用パスワード で生成してください"
    exit 1
fi

if [ -z "$NTFY_TOPIC" ]; then
    echo "⚠️  警告: NTFY_TOPIC が設定されていません（Push通知なし）"
fi

# 現在のバージョンを取得
VERSION=$(grep "^version:" pubspec.yaml | sed 's/version: //' | cut -d'+' -f1)
BUILD_NUMBER=$(grep "^version:" pubspec.yaml | sed 's/version: //' | cut -d'+' -f2)

echo ""
echo "📦 現在: $VERSION+$BUILD_NUMBER"

# Step 0: ビルド番号をインクリメント
NEW_BUILD_NUMBER=$((BUILD_NUMBER + 1))
echo "📈 更新後: $VERSION+$NEW_BUILD_NUMBER"

sed -i '' "s/^version: $VERSION+$BUILD_NUMBER/version: $VERSION+$NEW_BUILD_NUMBER/" pubspec.yaml

# 変更をコミット
git add pubspec.yaml
git commit -m "build: v$VERSION+$NEW_BUILD_NUMBER

Co-Authored-By: Claude <noreply@anthropic.com>"

BUILD_NUMBER=$NEW_BUILD_NUMBER
echo ""

# ビルド開始通知
send_notification "🔨 ビルド開始" "$APP_NAME v$VERSION+$BUILD_NUMBER のビルドを開始しました"

# Step 1: クリーンビルド
echo "🧹 Step 1/4: クリーンビルド..."
flutter clean
flutter pub get

# Step 2: iOS リリースビルド
echo ""
echo "🔨 Step 2/4: iOS IPAビルド..."
flutter build ipa --release

# IPA ファイルパスを取得
IPA_PATH=$(find build/ios/ipa -name "*.ipa" -type f 2>/dev/null | head -1)

if [ -z "$IPA_PATH" ] || [ ! -f "$IPA_PATH" ]; then
    echo "❌ エラー: IPAファイルが見つかりません"
    send_notification "❌ ビルド失敗" "IPAファイルが見つかりません" "high"
    exit 1
fi

echo "   ✅ IPA: $IPA_PATH"

# Step 3: App Store Connect にアップロード
echo ""
echo "🚀 Step 3/4: TestFlight へアップロード中..."

UPLOAD_CMD="xcrun altool --upload-app --type ios --file \"$IPA_PATH\" --username \"$APPLE_ID\" --password \"$APP_SPECIFIC_PASSWORD\""

if [ -n "$TEAM_ID" ]; then
    UPLOAD_CMD="$UPLOAD_CMD --team-id \"$TEAM_ID\""
fi

if eval $UPLOAD_CMD; then
    # アップロード成功通知
    send_notification "🚀 アップロード完了" "$APP_NAME v$VERSION+$BUILD_NUMBER をApp Store Connectにアップロードしました。約10分後にTestFlightで利用可能になります。" "high"

    # Step 4: 処理完了を待って通知（バックグラウンドで実行）
    echo ""
    echo "⏳ Appleの処理完了を待機中（バックグラウンド）..."
    (
        sleep 600  # 10分待機
        send_notification "✅ TestFlight準備完了" "$APP_NAME v$VERSION+$BUILD_NUMBER がTestFlightで利用可能になりました！" "high"
    ) &

    echo ""
    echo "=========================================="
    echo "✅ アップロード完了!"
    echo "=========================================="
    echo ""
    echo "📱 約10分後にPush通知が届きます"
    echo ""
    echo "バージョン: $VERSION+$BUILD_NUMBER"
    echo ""
else
    send_notification "❌ アップロード失敗" "TestFlightへのアップロードに失敗しました" "high"
    exit 1
fi
