#!/bin/bash
# Manual update script for DevGuard
# Run this script to pull latest code and restart the service
# Can be run via SSH or scheduled via cron

set -e

APP_DIR="/home/ubuntu/devguard"
SERVICE_NAME="devguard"

cd "$APP_DIR"

echo "🔄 Updating DevGuard..."
echo ""

# Pull latest changes
echo "📥 Checking for updates..."
git fetch origin

LATEST_COMMIT=$(git rev-parse origin/main 2>/dev/null || echo "")
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ -z "$LATEST_COMMIT" ] || [ -z "$CURRENT_COMMIT" ]; then
    echo "⚠️  Could not determine commit hashes, pulling anyway..."
    git pull origin main || {
        echo "❌ Git pull failed!"
        exit 1
    }
elif [ "$LATEST_COMMIT" = "$CURRENT_COMMIT" ]; then
    echo "✅ Already up to date (commit: ${CURRENT_COMMIT:0:7})"
    echo "   No restart needed."
    exit 0
else
    echo "📦 New updates available!"
    echo "   Current: ${CURRENT_COMMIT:0:7}"
    echo "   Latest:  ${LATEST_COMMIT:0:7}"
    echo ""
    echo "📥 Pulling changes..."
    git reset --hard origin/main
    git pull origin main
fi

echo ""
echo "📦 Installing/updating dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel

# Check disk space before installing
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "   ⚠️  Disk usage is ${DISK_USAGE}%, skipping heavy dependencies..."
    grep -v "sentence-transformers" requirements.txt > /tmp/requirements_safe.txt 2>/dev/null || cp requirements.txt /tmp/requirements_safe.txt
    pip install --quiet -r /tmp/requirements_safe.txt
else
    pip install --quiet -r requirements.txt || {
        echo "   ⚠️  Some dependencies failed, trying minimal set..."
        pip install --quiet streamlit langchain langchain-core langchain-community \
            langchain-google-genai google-genai pandas chardet boto3 python-dotenv
    }
fi

echo ""
echo "🔄 Restarting service..."
sudo systemctl restart ${SERVICE_NAME}
sleep 3

if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "✅ DevGuard updated and restarted successfully!"
    echo "   Latest commit: $(git rev-parse --short HEAD)"
else
    echo "⚠️  Service restart had issues. Check logs:"
    echo "   sudo journalctl -u ${SERVICE_NAME} -f"
    exit 1
fi

