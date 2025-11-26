#!/usr/bin/env python3
"""
Script to authorize Gmail/Calendar access and sync real data.
This will open a browser for OAuth authorization and then sync your accounts.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from backend.api.database import get_db, SessionLocal
from backend.integrations.gmail import GmailClient
from backend.integrations.calendar import CalendarClient
from backend.api.models import User, ConnectedAccount
import uuid


def get_or_create_user(db):
    """Get or create a default user."""
    user = db.query(User).first()
    if not user:
        user = User(id=uuid.uuid4(), email="default@example.com", name="Default User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def authorize_gmail(db, user):
    """Authorize Gmail access."""
    print("\n[AUTH] Authorizing Gmail Access...")
    print("A browser window will open for you to sign in and grant permissions.")

    gmail_secret_path = os.getenv("GMAIL_CLIENT_SECRET_PATH")
    if not gmail_secret_path or not os.path.exists(gmail_secret_path):
        print(f"[ERROR] Gmail credentials not found at: {gmail_secret_path}")
        return None

    try:
        client = GmailClient.authorize(gmail_secret_path)
        print("[OK] Gmail authorization successful!")

        # Get credentials
        creds = client.credentials

        # Check if account already exists
        account = (
            db.query(ConnectedAccount)
            .filter(ConnectedAccount.user_id == user.id, ConnectedAccount.provider == "gmail")
            .first()
        )

        if account:
            # Update existing account
            account.access_token = creds.token
            account.refresh_token = creds.refresh_token
            account.status = "active"
            account.raw_metadata = {
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
            }
            print("[OK] Updated existing Gmail account")
        else:
            # Create new account
            account = ConnectedAccount(
                id=uuid.uuid4(),
                user_id=user.id,
                provider="gmail",
                provider_account_id=creds.client_id,
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                status="active",
                raw_metadata={
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                },
            )
            db.add(account)
            print("[OK] Created new Gmail account connection")

        db.commit()
        return account

    except Exception as e:
        print(f"[ERROR] Gmail authorization failed: {e}")
        return None


def authorize_calendar(db, user):
    """Authorize Calendar access."""
    print("\n[AUTH] Authorizing Google Calendar Access...")
    print("A browser window will open for you to sign in and grant permissions.")

    calendar_secret_path = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET_PATH")
    if not calendar_secret_path or not os.path.exists(calendar_secret_path):
        print(f"[ERROR] Calendar credentials not found at: {calendar_secret_path}")
        return None

    try:
        client = CalendarClient.authorize(calendar_secret_path)
        print("[OK] Calendar authorization successful!")

        # Get credentials
        creds = client.credentials

        # Check if account already exists
        account = (
            db.query(ConnectedAccount)
            .filter(ConnectedAccount.user_id == user.id, ConnectedAccount.provider == "google_calendar")
            .first()
        )

        if account:
            # Update existing account
            account.access_token = creds.token
            account.refresh_token = creds.refresh_token
            account.status = "active"
            account.raw_metadata = {
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
            }
            print("[OK] Updated existing Calendar account")
        else:
            # Create new account
            account = ConnectedAccount(
                id=uuid.uuid4(),
                user_id=user.id,
                provider="google_calendar",
                provider_account_id=creds.client_id,
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                status="active",
                raw_metadata={
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                },
            )
            db.add(account)
            print("[OK] Created new Calendar account connection")

        db.commit()
        return account

    except Exception as e:
        print(f"[ERROR] Calendar authorization failed: {e}")
        return None


def sync_accounts(db, user):
    """Sync data from connected accounts."""
    from backend.ingestion.sync_service import SyncService

    print("\n[SYNC] Syncing data from connected accounts...")
    sync_service = SyncService(db)

    results = sync_service.sync_all_accounts(str(user.id))

    print("\n[RESULTS] Sync Results:")
    for provider, count in results.items():
        if isinstance(count, int):
            print(f"  {provider}: {count} items synced")
        else:
            print(f"  {provider}: {count}")

    return results


def main():
    print("=" * 60)
    print("  Personal Ops Center - Account Authorization & Sync")
    print("=" * 60)

    db = SessionLocal()
    try:
        # Get or create user
        user = get_or_create_user(db)
        print(f"\n[USER] Using user: {user.email}")

        # Authorize accounts
        gmail_account = authorize_gmail(db, user)
        calendar_account = authorize_calendar(db, user)

        if gmail_account or calendar_account:
            # Sync data
            sync_accounts(db, user)
            print("\n[OK] Setup complete! Your inbox should now show real data.")
        else:
            print("\n[WARNING] No accounts were authorized. Please check your OAuth credentials.")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
