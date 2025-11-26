# Google Cloud Console Setup Guide

Complete step-by-step guide to configure Gmail API and Google Calendar API for Personal Ops Center.

## 📋 Prerequisites

- Google account (Gmail account)
- Access to Google Cloud Console

---

## 🚀 Step-by-Step Setup

### Step 1: Access Google Cloud Console

1. Go to: **https://console.cloud.google.com/**
2. Sign in with your Google account

### Step 2: Create a New Project

1. Click the **project dropdown** at the top of the page (next to "Google Cloud")
2. Click **"New Project"**
3. Fill in:
   - **Project name**: `Personal Ops Center` (or any name you prefer)
   - **Organization**: Leave as default (if applicable)
   - **Location**: Leave as default
4. Click **"Create"**
5. Wait for the project to be created (usually a few seconds)
6. Select your new project from the dropdown if it's not already selected

### Step 3: Enable Required APIs

You need to enable two APIs:

#### Enable Gmail API:
1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. In the search bar, type: **"Gmail API"**
3. Click on **"Gmail API"** from the results
4. Click the **"Enable"** button
5. Wait for it to enable (you'll see a checkmark when done)

#### Enable Google Calendar API:
1. Still in **"APIs & Services"** → **"Library"**
2. In the search bar, type: **"Google Calendar API"**
3. Click on **"Google Calendar API"** from the results
4. Click the **"Enable"** button
5. Wait for it to enable

**✅ Verification**: You should see both APIs listed under **"APIs & Services"** → **"Enabled APIs"**

### Step 4: Configure OAuth Consent Screen

This is required before creating OAuth credentials:

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** (unless you have a Google Workspace account)
3. Click **"Create"**

#### Fill in App Information:
- **App name**: `Personal Ops Center`
- **User support email**: Select your email from dropdown
- **App logo**: (Optional - skip for now)
- **Application home page**: `http://localhost:3101` (or leave blank)
- **Application privacy policy link**: (Optional - skip)
- **Application terms of service link**: (Optional - skip)
- **Authorized domains**: (Leave empty for now)
- **Developer contact information**: Your email

Click **"Save and Continue"**

#### Scopes (Step 2):
1. Click **"Add or Remove Scopes"**
2. In the filter box, search for and add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/calendar`
3. Click **"Update"**
4. Click **"Save and Continue"**

#### Test Users (Step 3):
1. Click **"Add Users"**
2. Enter your Gmail address (the one you'll use with the app)
3. Click **"Add"**
4. Click **"Save and Continue"**

#### Summary (Step 4):
- Review the information
- Click **"Back to Dashboard"**

**⚠️ Important**: Your app will be in "Testing" mode. This means only the test users you added can use it. This is fine for personal use.

### Step 5: Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** at the top
3. Select **"OAuth client ID"**

#### If prompted about OAuth consent screen:
- Click **"Configure Consent Screen"** if you haven't completed Step 4
- Otherwise, select your OAuth consent screen and continue

#### Create OAuth Client:
- **Application type**: Select **"Desktop app"**
- **Name**: `Personal Ops Center - Desktop`
- Click **"Create"**

#### Download Credentials:
1. A popup will appear with your **Client ID** and **Client Secret**
2. **⚠️ IMPORTANT**: Click **"Download JSON"** button
3. Save the file somewhere you can find it (e.g., Downloads folder)
4. The file will be named something like: `client_secret_xxxxx.apps.googleusercontent.com.json`
5. Click **"OK"** to close the popup

**✅ You now have OAuth credentials!**

### Step 6: Install Credentials in Your Project

Run the setup script:

```bash
cd /home/oneknight/personal/multiagents
./setup_google_oauth.sh
```

When prompted, provide the path to your downloaded JSON file.

**OR** manually:

```bash
# Copy the downloaded file to secrets directory
cp ~/Downloads/client_secret_*.json secrets/gmail_client_secret.json
cp ~/Downloads/client_secret_*.json secrets/calendar_client_secret.json

# Set proper permissions
chmod 600 secrets/*.json
```

### Step 7: Verify Setup

Check that everything is configured:

```bash
# Check secrets directory
ls -la secrets/

# Should show:
# gmail_client_secret.json
# calendar_client_secret.json

# Verify .env paths
grep -E "GMAIL_CLIENT_SECRET_PATH|GOOGLE_CALENDAR_CLIENT_SECRET_PATH" .env
```

---

## 🎯 Quick Checklist

- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Enabled Google Calendar API
- [ ] Configured OAuth consent screen
- [ ] Added test user (your email)
- [ ] Created OAuth client ID (Desktop app)
- [ ] Downloaded credentials JSON file
- [ ] Copied JSON to `secrets/` directory
- [ ] Updated `.env` file (already done)
- [ ] Set file permissions (600)

---

## 🔍 Verification Commands

```bash
# Check if APIs are enabled (from Google Cloud Console)
# Go to: APIs & Services → Enabled APIs
# Should see: Gmail API, Google Calendar API

# Check credentials file format
cat secrets/gmail_client_secret.json | head -5
# Should show JSON with "installed" key containing client_id, client_secret, etc.

# Check .env configuration
grep -E "GMAIL|CALENDAR" .env | grep CLIENT_SECRET_PATH
```

---

## 🐛 Common Issues & Solutions

### Issue: "OAuth client ID creation disabled"
**Solution**: Complete the OAuth consent screen configuration first (Step 4)

### Issue: "Redirect URI mismatch"
**Solution**: Make sure you selected **"Desktop app"** (not Web application)

### Issue: "Access blocked: This app's request is invalid"
**Solution**: 
- Make sure you added your email as a test user
- Check that OAuth consent screen is published (or in Testing mode with your email added)

### Issue: "API not enabled"
**Solution**: Go to APIs & Services → Library → Search for the API → Enable it

### Issue: "Invalid credentials file"
**Solution**: 
- Make sure you downloaded the JSON file (not just copied Client ID/Secret)
- Verify the file path in `.env` is correct and absolute
- Check file permissions: `chmod 600 secrets/*.json`

---

## 📚 Additional Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

---

## ✅ Next Steps

Once setup is complete:

1. **Start your application**
2. **First authorization**: The app will open a browser window
3. **Sign in**: Use the Google account you added as a test user
4. **Grant permissions**: Allow access to Gmail and Calendar
5. **Done**: Tokens will be saved for future use

Your Personal Ops Center is now ready to access Gmail and Google Calendar! 🎉

