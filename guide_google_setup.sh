#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "  Google Cloud Console Setup Guide"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This guide will walk you through configuring Google APIs."
echo ""
read -p "Press Enter to continue..."

echo ""
echo "📋 STEP 1: Access Google Cloud Console"
echo "───────────────────────────────────────"
echo "1. Open your browser"
echo "2. Go to: https://console.cloud.google.com/"
echo "3. Sign in with your Google account"
echo ""
read -p "Have you signed in? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please sign in first, then run this script again."
    exit 1
fi

echo ""
echo "📋 STEP 2: Create a New Project"
echo "────────────────────────────────"
echo "1. Click the project dropdown (top of page, next to 'Google Cloud')"
echo "2. Click 'New Project'"
echo "3. Enter project name: 'Personal Ops Center'"
echo "4. Click 'Create'"
echo "5. Wait for project creation, then select it from dropdown"
echo ""
read -p "Have you created the project? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please create the project first."
    exit 1
fi

echo ""
echo "📋 STEP 3: Enable APIs"
echo "──────────────────────"
echo "1. Go to: APIs & Services → Library"
echo "2. Search for 'Gmail API' → Click it → Click 'Enable'"
echo "3. Go back to Library"
echo "4. Search for 'Google Calendar API' → Click it → Click 'Enable'"
echo ""
read -p "Have you enabled both APIs? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please enable both APIs first."
    exit 1
fi

echo ""
echo "📋 STEP 4: Configure OAuth Consent Screen"
echo "───────────────────────────────────────────"
echo "1. Go to: APIs & Services → OAuth consent screen"
echo "2. Select 'External' → Click 'Create'"
echo "3. Fill in:"
echo "   - App name: Personal Ops Center"
echo "   - User support email: (select your email)"
echo "   - Developer contact: (your email)"
echo "4. Click 'Save and Continue'"
echo "5. Click 'Add or Remove Scopes'"
echo "6. Add these scopes:"
echo "   • https://www.googleapis.com/auth/gmail.readonly"
echo "   • https://www.googleapis.com/auth/gmail.compose"
echo "   • https://www.googleapis.com/auth/calendar"
echo "7. Click 'Update' → 'Save and Continue'"
echo "8. Add your email as a test user → 'Save and Continue'"
echo "9. Review and click 'Back to Dashboard'"
echo ""
read -p "Have you configured the OAuth consent screen? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please complete the OAuth consent screen configuration."
    exit 1
fi

echo ""
echo "📋 STEP 5: Create OAuth Credentials"
echo "───────────────────────────────────"
echo "1. Go to: APIs & Services → Credentials"
echo "2. Click '+ Create Credentials' → 'OAuth client ID'"
echo "3. Application type: Select 'Desktop app'"
echo "4. Name: 'Personal Ops Center - Desktop'"
echo "5. Click 'Create'"
echo "6. IMPORTANT: Click 'Download JSON'"
echo "7. Save the file (remember where!)"
echo "8. Click 'OK'"
echo ""
read -p "Have you downloaded the credentials JSON file? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please download the credentials file first."
    exit 1
fi

echo ""
echo "📋 STEP 6: Install Credentials"
echo "──────────────────────────────"
read -p "Enter the path to your downloaded JSON file: " JSON_PATH

if [ ! -f "$JSON_PATH" ]; then
    echo "❌ File not found: $JSON_PATH"
    echo "Please check the path and try again."
    exit 1
fi

# Copy to secrets directory
mkdir -p secrets
cp "$JSON_PATH" secrets/gmail_client_secret.json
cp "$JSON_PATH" secrets/calendar_client_secret.json
chmod 600 secrets/*.json

echo "✅ Credentials installed successfully!"

# Update .env
ENV_FILE=".env"
GMAIL_PATH="$(pwd)/secrets/gmail_client_secret.json"
CALENDAR_PATH="$(pwd)/secrets/calendar_client_secret.json"

if [ -f "$ENV_FILE" ]; then
    sed -i "s|^GMAIL_CLIENT_SECRET_PATH=.*|GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH|" "$ENV_FILE"
    sed -i "s|^GOOGLE_CALENDAR_CLIENT_SECRET_PATH=.*|GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH|" "$ENV_FILE"
    echo "✅ Updated .env file"
else
    echo "⚠️  .env file not found. Please update manually:"
    echo "GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH"
    echo "GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH"
fi

echo ""
echo "🎉 Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Start your application"
echo "2. When prompted, authorize access in your browser"
echo "3. Sign in with your Google account"
echo "4. Grant permissions for Gmail and Calendar"
echo ""
echo "Your Personal Ops Center is ready! 🚀"

