#!/bin/bash
# fi-tracker deploy script
set -e

APP_NAME="fi-tracker-familieidraet"
VOLUME_NAME="fi_tracker_data"
REGION="arn"

echo "🚀 Deploying fi-tracker to Fly.io"

# 1. Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install it first: brew install flyctl"
    exit 1
fi

# 2. Check if fly app exists, if not create it + volume
if ! flyctl status --app "$APP_NAME" &> /dev/null; then
    echo "📦 Creating app: $APP_NAME"
    flyctl apps create "$APP_NAME"
    
    echo "💾 Creating volume: $VOLUME_NAME"
    flyctl volumes create "$VOLUME_NAME" --region "$REGION" --size 1 --app "$APP_NAME"
fi

# 3. Prompt for optional BASIC_AUTH_PASSWORD
echo ""
echo "🔐 Basic auth (optional)"
echo -n "Enter BASIC_AUTH_PASSWORD (press Enter to skip): "
read -rs BASIC_AUTH_PASSWORD
echo ""

# 4. If password provided, set as secret
if [ -n "$BASIC_AUTH_PASSWORD" ]; then
    echo "🔒 Setting BASIC_AUTH_PASSWORD secret..."
    flyctl secrets set BASIC_AUTH_PASSWORD="$BASIC_AUTH_PASSWORD" --app "$APP_NAME"
fi

# 5. Run flyctl deploy
echo "🛫 Deploying..."
flyctl deploy --app "$APP_NAME"

# 6. Print the app URL
echo ""
echo "✅ Deployed!"
echo "🌐 URL: https://$APP_NAME.fly.dev"
