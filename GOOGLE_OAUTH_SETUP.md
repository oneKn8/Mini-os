# Google OAuth Setup Guide

This guide will help you set up Gmail and Google Calendar OAuth credentials for your Personal Ops Center.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "Personal Ops Center")
5. Click **"Create"**

## Step 2: Enable Required APIs

1. In your Google Cloud project, go to **"APIs & Services" > "Library"**
2. Search for and enable these APIs:
   - **Gmail API**
   - **Google Calendar API**

## Step 3: Create OAuth Credentials

### Option A: Single OAuth Client (Recommended - Can use same credentials for both)

1. Go to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials" > "OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - Choose **"External"** (unless you have a Google Workspace)
   - Fill in:
     - App name: "Personal Ops Center"
     - User support email: Your email
     - Developer contact: Your email
   - Click **"Save and Continue"** through the scopes (you can add them later)
   - Add your email as a test user
   - Click **"Save and Continue"** to finish

4. Back in Credentials, select **"Desktop app"** as the application type
5. Name it: "Personal Ops Center - Desktop"
6. Click **"Create"**
7. Click **"Download JSON"** - Save this file as `google_oauth_credentials.json`

### Option B: Separate OAuth Clients (If you prefer separate credentials)

**For Gmail:**
1. Create OAuth client ID
2. Application type: **Desktop app**
3. Name: "Personal Ops Center - Gmail"
4. Download as `gmail_client_secret.json`

**For Calendar:**
1. Create another OAuth client ID
2. Application type: **Desktop app**
3. Name: "Personal Ops Center - Calendar"
4. Download as `calendar_client_secret.json`

## Step 4: Place Credentials in Secrets Directory

Copy your downloaded JSON file(s) to the `secrets/` directory:

```bash
# If using single credentials file (Option A):
cp ~/Downloads/google_oauth_credentials.json secrets/gmail_client_secret.json
cp ~/Downloads/google_oauth_credentials.json secrets/calendar_client_secret.json

# If using separate files (Option B):
cp ~/Downloads/gmail_client_secret.json secrets/
cp ~/Downloads/calendar_client_secret.json secrets/
```

## Step 5: Update .env File

Update your `.env` file with the absolute paths to the credential files:

```bash
# For single credentials file:
GMAIL_CLIENT_SECRET_PATH=/home/oneknight/personal/multiagents/secrets/gmail_client_secret.json
GOOGLE_CALENDAR_CLIENT_SECRET_PATH=/home/oneknight/personal/multiagents/secrets/calendar_client_secret.json

# Or if using separate files, use their respective paths
```

## Step 6: Set Proper Permissions

Make sure the secrets directory and files have appropriate permissions:

```bash
chmod 700 secrets/
chmod 600 secrets/*.json
```

## Step 7: First-Time Authorization

When you first run the application, it will:
1. Open a browser window for OAuth authorization
2. Ask you to sign in with your Google account
3. Request permissions for Gmail and Calendar access
4. Save the tokens for future use

## Troubleshooting

### "Redirect URI mismatch" error
- Make sure you selected **"Desktop app"** as the application type
- The OAuth flow uses `localhost` redirects automatically

### "Access blocked" error
- Make sure you added your email as a test user in the OAuth consent screen
- If your app is in "Testing" mode, only test users can access it

### "Invalid credentials" error
- Verify the JSON file paths in `.env` are correct and absolute
- Check that the JSON files are valid and not corrupted

## Security Notes

- Never commit the `secrets/` directory to git (it's already in `.gitignore`)
- Keep your OAuth credentials secure
- Rotate credentials if they're ever compromised
- The credentials JSON contains your Client ID and Client Secret - treat them as sensitive

