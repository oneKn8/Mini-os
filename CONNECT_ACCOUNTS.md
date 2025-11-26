# Connecting Your Gmail and Calendar Accounts

To sync real data instead of dummy data, you need to connect your Gmail and Google Calendar accounts.

## Step 1: Authorize Gmail Access

The first time you use Gmail features, the app will need to authorize access:

1. **Start the OAuth flow** - This happens automatically when you try to sync
2. **A browser window will open** - Sign in with your Google account
3. **Grant permissions** - Allow the app to:
   - Read your Gmail messages
   - Create email drafts
   - Access your Google Calendar

## Step 2: Manual Authorization (If Needed)

If automatic authorization doesn't work, you can authorize manually:

```python
# Run this in Python to authorize Gmail
from backend.integrations.gmail import GmailClient
import os

# Use the credentials file we set up earlier
client = GmailClient.authorize('/home/oneknight/personal/multiagents/secrets/gmail_client_secret.json')

# This will:
# 1. Open a browser window
# 2. Ask you to sign in
# 3. Request permissions
# 4. Save tokens for future use
```

## Step 3: Trigger Sync

Once authorized, trigger a sync to fetch real data:

### Via API:
```bash
# Sync Gmail
curl -X POST http://localhost:8101/api/sync/trigger?provider=gmail

# Sync Calendar
curl -X POST http://localhost:8101/api/sync/trigger?provider=google_calendar

# Sync everything
curl -X POST http://localhost:8101/api/sync/trigger
```

### Via Python Script:
```python
from backend.api.database import get_db
from backend.ingestion.sync_service import SyncService

db = next(get_db())
sync_service = SyncService(db)

# Sync all accounts for a user
results = sync_service.sync_all_accounts(user_id="your_user_id")
print(results)
```

## Current Status

Right now, you're seeing dummy/test data because:
1. ✅ OAuth credentials are configured
2. ❌ Accounts haven't been connected yet
3. ❌ No sync has been triggered

## Next Steps

1. **Connect your accounts** - The app needs to authorize access first
2. **Trigger sync** - Once connected, sync will fetch real emails/events
3. **View real data** - Your inbox will show actual emails and calendar events

## Troubleshooting

**"No accounts connected"**
- Run the authorization flow first
- Check that OAuth credentials are in `secrets/` directory

**"Sync returns 0 items"**
- Verify you've granted permissions
- Check that your account has emails/events
- Check backend logs for errors

**"Authorization fails"**
- Verify OAuth credentials JSON file exists
- Check that you added your email as a test user in Google Cloud Console
- Make sure OAuth consent screen is configured

