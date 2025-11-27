"""
Account connection and management API routes.
"""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import ConnectedAccount, User
from backend.integrations.gmail import GmailClient
from backend.integrations.calendar import CalendarClient

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _get_or_create_default_user(db: Session) -> User:
    """Ensure a user exists so local dev works without auth."""
    user = db.query(User).first()
    if user:
        return user

    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        name="Default User",
        password_hash="dev-placeholder",
        timezone="UTC",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/connected")
async def get_connected_accounts(db: Session = Depends(get_db)):
    """Get all connected accounts for the current user."""
    # TODO: Get user from session/auth token
    user = _get_or_create_default_user(db)

    accounts = (
        db.query(ConnectedAccount)
        .filter(ConnectedAccount.user_id == user.id, ConnectedAccount.status == "active")
        .all()
    )

    return [
        {
            "id": str(acc.id),
            "provider": acc.provider,
            "provider_email": acc.provider_email,
            "status": acc.status,
            "last_sync_at": acc.last_sync_at.isoformat() if acc.last_sync_at else None,
        }
        for acc in accounts
    ]


@router.post("/connect/gmail")
async def connect_gmail(db: Session = Depends(get_db)):
    """Initiate Gmail OAuth connection."""
    import threading

    gmail_secret_path = os.getenv("GMAIL_CLIENT_SECRET_PATH")
    if not gmail_secret_path or not os.path.exists(gmail_secret_path):
        raise HTTPException(status_code=500, detail="Gmail OAuth credentials not configured")

    # TODO: Get user from session/auth token
    user = _get_or_create_default_user(db)

    def authorize_in_background():
        """Run OAuth flow in background thread."""
        try:
            # Create a new database session for this thread
            from backend.api.database import SessionLocal

            thread_db = SessionLocal()

            try:
                # This will open a browser for OAuth (blocking call)
                client = GmailClient.authorize(gmail_secret_path)
                creds = client.credentials

                # Get user again in this thread
                thread_user = thread_db.query(User).filter(User.id == user.id).first()
                if not thread_user:
                    return

                # Check if account exists
                account = (
                    thread_db.query(ConnectedAccount)
                    .filter(ConnectedAccount.user_id == thread_user.id, ConnectedAccount.provider == "gmail")
                    .first()
                )

                # Read client credentials from JSON file
                import json

                with open(gmail_secret_path) as f:
                    creds_data = json.load(f)
                    client_id = creds_data["installed"]["client_id"]
                    client_secret = creds_data["installed"]["client_secret"]

                if account:
                    account.access_token = creds.token
                    account.refresh_token = creds.refresh_token
                    account.status = "active"
                    account.scopes = {"client_id": client_id, "client_secret": client_secret}
                else:
                    account = ConnectedAccount(
                        user_id=thread_user.id,
                        provider="gmail",
                        provider_account_id=client_id,
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        status="active",
                        scopes={"client_id": client_id, "client_secret": client_secret},
                    )
                    thread_db.add(account)

                thread_db.commit()

                # Auto-sync after connection
                from backend.ingestion.sync_service import SyncService

                sync_service = SyncService(thread_db)
                sync_service.sync_gmail(account)
            finally:
                thread_db.close()
        except Exception as e:
            print(f"Background OAuth error: {e}")

    # Start OAuth in background thread
    thread = threading.Thread(target=authorize_in_background, daemon=True)
    thread.start()

    # Return immediately - OAuth will happen in background
    return {
        "status": "initiated",
        "provider": "gmail",
        "message": "A browser window should open for authorization. Please complete the OAuth flow there.",
    }


@router.post("/connect/calendar")
async def connect_calendar(db: Session = Depends(get_db)):
    """Initiate Google Calendar OAuth connection."""
    import threading

    calendar_secret_path = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET_PATH")
    if not calendar_secret_path or not os.path.exists(calendar_secret_path):
        raise HTTPException(status_code=500, detail="Calendar OAuth credentials not configured")

    # TODO: Get user from session/auth token
    user = _get_or_create_default_user(db)

    def authorize_in_background():
        """Run OAuth flow in background thread."""
        try:
            # Create a new database session for this thread
            from backend.api.database import SessionLocal

            thread_db = SessionLocal()

            try:
                # This will open a browser for OAuth (blocking call)
                client = CalendarClient.authorize(calendar_secret_path)
                creds = client.credentials

                # Get user again in this thread
                thread_user = thread_db.query(User).filter(User.id == user.id).first()
                if not thread_user:
                    return

                # Check if account exists
                account = (
                    thread_db.query(ConnectedAccount)
                    .filter(ConnectedAccount.user_id == thread_user.id, ConnectedAccount.provider == "google_calendar")
                    .first()
                )

                # Read client credentials from JSON file
                import json

                with open(calendar_secret_path) as f:
                    creds_data = json.load(f)
                    client_id = creds_data["installed"]["client_id"]
                    client_secret = creds_data["installed"]["client_secret"]

                if account:
                    account.access_token = creds.token
                    account.refresh_token = creds.refresh_token
                    account.status = "active"
                    account.scopes = {"client_id": client_id, "client_secret": client_secret}
                else:
                    account = ConnectedAccount(
                        user_id=thread_user.id,
                        provider="google_calendar",
                        provider_account_id=client_id,
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        status="active",
                        scopes={"client_id": client_id, "client_secret": client_secret},
                    )
                    thread_db.add(account)

                thread_db.commit()

                # Auto-sync after connection
                from backend.ingestion.sync_service import SyncService

                sync_service = SyncService(thread_db)
                sync_service.sync_calendar(account)
            finally:
                thread_db.close()
        except Exception as e:
            print(f"Background OAuth error: {e}")

    # Start OAuth in background thread
    thread = threading.Thread(target=authorize_in_background, daemon=True)
    thread.start()

    # Return immediately - OAuth will happen in background
    return {
        "status": "initiated",
        "provider": "google_calendar",
        "message": "A browser window should open for authorization. Please complete the OAuth flow there.",
    }


@router.delete("/disconnect/{provider}")
async def disconnect_account(provider: str, db: Session = Depends(get_db)):
    """Disconnect an account."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    account = (
        db.query(ConnectedAccount)
        .filter(ConnectedAccount.user_id == user.id, ConnectedAccount.provider == provider)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.status = "revoked"
    db.commit()

    return {"status": "disconnected", "provider": provider}
