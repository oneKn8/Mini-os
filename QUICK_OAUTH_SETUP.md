# Quick Google OAuth Setup

## 🚀 Fast Track Setup (5 minutes)

### Step 1: Get OAuth Credentials
1. Visit: https://console.cloud.google.com/
2. Create/Select project → Enable **Gmail API** + **Google Calendar API**
3. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
4. Configure OAuth consent screen (if first time):
   - App name: "Personal Ops Center"
   - Your email as support/developer contact
   - Add your email as test user
5. Create OAuth client:
   - Type: **Desktop app**
   - Name: "Personal Ops Center"
   - **Download JSON**

### Step 2: Run Setup Script
```bash
./setup_google_oauth.sh
```
Follow the prompts and provide the path to your downloaded JSON file.

### Step 3: Done! ✅
The script will:
- ✅ Copy credentials to `secrets/` directory
- ✅ Update `.env` file with correct paths
- ✅ Set proper file permissions

### Step 4: First Authorization
When you start the app, it will:
1. Open browser for Google sign-in
2. Request Gmail & Calendar permissions
3. Save tokens for future use

---

## 📋 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Copy your downloaded JSON to secrets directory
cp ~/Downloads/your-credentials.json secrets/gmail_client_secret.json
cp ~/Downloads/your-credentials.json secrets/calendar_client_secret.json

# 2. Set permissions
chmod 700 secrets/
chmod 600 secrets/*.json

# 3. Update .env (already done, but verify):
# GMAIL_CLIENT_SECRET_PATH=/home/oneknight/personal/multiagents/secrets/gmail_client_secret.json
# GOOGLE_CALENDAR_CLIENT_SECRET_PATH=/home/oneknight/personal/multiagents/secrets/calendar_client_secret.json
```

---

## 🔍 Verify Setup

```bash
# Check secrets directory
ls -la secrets/

# Check .env paths
grep -E "GMAIL_CLIENT_SECRET_PATH|GOOGLE_CALENDAR_CLIENT_SECRET_PATH" .env

# Both should show absolute paths to JSON files
```

---

## ❓ Troubleshooting

**"Redirect URI mismatch"**
→ Make sure you selected **Desktop app** (not Web application)

**"Access blocked"**
→ Add your email as a test user in OAuth consent screen

**"File not found"**
→ Verify paths in `.env` are absolute and correct

---

For detailed instructions, see `GOOGLE_OAUTH_SETUP.md`

