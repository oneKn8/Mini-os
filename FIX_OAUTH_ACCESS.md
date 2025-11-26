# Fix: "Access blocked" Error

You're seeing this error because your OAuth app is in **Testing** mode and your email isn't added as a test user.

## Quick Fix (2 minutes)

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Select your project ("Personal Ops Center" or whatever you named it)

### Step 2: Add Your Email as Test User
1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Scroll down to **"Test users"** section
3. Click **"+ ADD USERS"**
4. Enter your email: **shifatsanto75@gmail.com**
5. Click **"Add"**
6. Click **"Save"**

### Step 3: Try Again
1. Go back to your Settings page
2. Click "Connect" for Gmail/Calendar again
3. It should work now!

## Why This Happened

When you created the OAuth consent screen, you selected "External" which puts the app in Testing mode. In Testing mode:
- Only test users you explicitly add can authorize the app
- This is perfect for personal use - you don't need to verify your app publicly

## Alternative: Publish Your App (Not Recommended for Personal Use)

If you want anyone to use it (not just you):
1. Go to OAuth consent screen
2. Click **"PUBLISH APP"** button
3. This requires app verification if you have sensitive scopes
4. **Not recommended** for personal use - just add yourself as a test user instead

## Quick Checklist

- [ ] Go to Google Cloud Console
- [ ] APIs & Services → OAuth consent screen
- [ ] Add shifatsanto75@gmail.com as test user
- [ ] Save
- [ ] Try connecting again

That's it! Once you add your email, the authorization will work.

