# OAuth Consent Screen - Next Steps

You're currently at **Step 2: Audience** and have correctly selected **"External"**.

## ✅ What You've Completed:
- Step 1: App Information ✓
- Step 2: Audience (External selected) ← You are here

## 📋 Next Steps:

### Step 3: Scopes
After clicking "Next", you'll be asked to add scopes. Add these:

1. Click **"Add or Remove Scopes"**
2. In the filter/search box, search for and add:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/calendar`
3. Click **"Update"**
4. Click **"Save and Continue"**

### Step 4: Test Users
1. Click **"Add Users"**
2. Enter your Gmail address (the one you'll use with the app)
3. Click **"Add"**
4. Click **"Save and Continue"**

### Step 5: Summary
1. Review the information
2. Click **"Back to Dashboard"**

## ⚠️ Important Notes:

- **Testing Mode**: Your app will be in "Testing" mode, which means only the test users you add can use it. This is perfect for personal use.

- **No Verification Needed**: For personal/testing use, you don't need to verify your app with Google.

- **Test Users**: Make sure to add your own email address as a test user, otherwise you won't be able to authorize the app.

## 🎯 After Completing OAuth Consent Screen:

1. Go to **"APIs & Services" → "Credentials"**
2. Click **"+ Create Credentials" → "OAuth client ID"**
3. Select **"Desktop app"** as application type
4. Name it: "Personal Ops Center - Desktop"
5. Click **"Create"**
6. **Download the JSON file** (very important!)
7. Run: `./setup_google_oauth.sh` and provide the path to the downloaded JSON

You're doing great! Continue with the steps above. 🚀

