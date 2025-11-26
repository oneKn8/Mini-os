#!/bin/bash

# Google OAuth Setup Helper Script
# This script helps you configure Google OAuth credentials

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="$SCRIPT_DIR/secrets"

echo "🔐 Google OAuth Setup Helper"
echo "============================"
echo ""

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"

echo "📁 Secrets directory: $SECRETS_DIR"
echo ""

# Check if credentials files already exist
if [ -f "$SECRETS_DIR/gmail_client_secret.json" ] || [ -f "$SECRETS_DIR/calendar_client_secret.json" ]; then
    echo "⚠️  Warning: OAuth credential files already exist in secrets/"
    read -p "Do you want to overwrite them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing files. Exiting."
        exit 0
    fi
fi

echo "Please follow these steps:"
echo ""
echo "1. Go to: https://console.cloud.google.com/"
echo "2. Create a new project (or select existing)"
echo "3. Enable 'Gmail API' and 'Google Calendar API'"
echo "4. Go to 'APIs & Services' > 'Credentials'"
echo "5. Create OAuth Client ID (Application type: Desktop app)"
echo "6. Download the JSON credentials file"
echo ""
read -p "Press Enter when you've downloaded the credentials JSON file..."

# Ask for the downloaded file location
echo ""
read -p "Enter the path to your downloaded credentials JSON file: " CREDENTIALS_PATH

if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "❌ Error: File not found at $CREDENTIALS_PATH"
    exit 1
fi

# Copy credentials to secrets directory
echo ""
echo "📋 Copying credentials to secrets directory..."

# Option 1: Use same file for both (recommended)
cp "$CREDENTIALS_PATH" "$SECRETS_DIR/gmail_client_secret.json"
cp "$CREDENTIALS_PATH" "$SECRETS_DIR/calendar_client_secret.json"

# Set proper permissions
chmod 600 "$SECRETS_DIR"/*.json

echo "✅ Credentials copied successfully!"
echo ""

# Update .env file
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: .env file not found. Creating from env.example..."
    cp "$SCRIPT_DIR/env.example" "$ENV_FILE"
fi

echo "📝 Updating .env file..."

# Get absolute paths
GMAIL_PATH="$SECRETS_DIR/gmail_client_secret.json"
CALENDAR_PATH="$SECRETS_DIR/calendar_client_secret.json"

# Update .env file using sed
if grep -q "^GMAIL_CLIENT_SECRET_PATH=" "$ENV_FILE"; then
    sed -i "s|^GMAIL_CLIENT_SECRET_PATH=.*|GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH|" "$ENV_FILE"
else
    echo "GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH" >> "$ENV_FILE"
fi

if grep -q "^GOOGLE_CALENDAR_CLIENT_SECRET_PATH=" "$ENV_FILE"; then
    sed -i "s|^GOOGLE_CALENDAR_CLIENT_SECRET_PATH=.*|GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH|" "$ENV_FILE"
else
    echo "GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH" >> "$ENV_FILE"
fi

echo "✅ .env file updated!"
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your OAuth consent screen is configured"
echo "2. Add your email as a test user (if app is in testing mode)"
echo "3. Restart your application"
echo ""
echo "When you first run the app, it will open a browser for OAuth authorization."

