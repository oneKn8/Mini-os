#!/bin/bash

# Helper script to manually create OAuth credentials JSON file
# Use this if the download button doesn't work

echo "═══════════════════════════════════════════════════════════"
echo "  OAuth Credentials Setup Helper"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "If the download button didn't work, you can manually create"
echo "the credentials file using the Client ID and Secret."
echo ""

read -p "Enter your Client ID: " CLIENT_ID
read -p "Enter your Client Secret: " CLIENT_SECRET

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Error: Both Client ID and Secret are required"
    exit 1
fi

# Create the JSON structure
JSON_FILE="secrets/gmail_client_secret.json"
mkdir -p secrets

cat > "$JSON_FILE" << EOF
{
  "installed": {
    "client_id": "$CLIENT_ID",
    "project_id": "personal-ops-center",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "$CLIENT_SECRET",
    "redirect_uris": [
      "http://localhost"
    ]
  }
}
EOF

# Copy to calendar as well
cp "$JSON_FILE" secrets/calendar_client_secret.json

# Set permissions
chmod 600 secrets/*.json

echo ""
echo "✅ Credentials file created successfully!"
echo "   Location: $JSON_FILE"
echo ""
echo "📝 Updating .env file..."

# Update .env
ENV_FILE=".env"
GMAIL_PATH="$(pwd)/secrets/gmail_client_secret.json"
CALENDAR_PATH="$(pwd)/secrets/calendar_client_secret.json"

if [ -f "$ENV_FILE" ]; then
    sed -i "s|^GMAIL_CLIENT_SECRET_PATH=.*|GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH|" "$ENV_FILE"
    sed -i "s|^GOOGLE_CALENDAR_CLIENT_SECRET_PATH=.*|GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH|" "$ENV_FILE"
    echo "✅ .env file updated!"
else
    echo "⚠️  .env file not found. Please add these lines manually:"
    echo "GMAIL_CLIENT_SECRET_PATH=$GMAIL_PATH"
    echo "GOOGLE_CALENDAR_CLIENT_SECRET_PATH=$CALENDAR_PATH"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "You can find your credentials later in:"
echo "Google Cloud Console → APIs & Services → Credentials"
echo ""

