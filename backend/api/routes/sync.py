"""
Sync API routes for triggering data synchronization from external providers.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import User, ConnectedAccount
from backend.api.sse import emit_inbox_update, emit_calendar_update
from backend.ingestion.sync_service import SyncService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger")
async def trigger_sync(provider: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Manually trigger a sync for one or all providers.

    Args:
        provider: Optional provider filter (gmail, outlook, google_calendar)
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    sync_service = SyncService(db)

    try:
        if provider:
            # Sync specific provider
            account = (
                db.query(ConnectedAccount)
                .filter(
                    ConnectedAccount.user_id == user.id,
                    ConnectedAccount.provider == provider,
                    ConnectedAccount.status == "active",
                )
                .first()
            )

            if not account:
                raise HTTPException(status_code=404, detail=f"No active {provider} account found")

            if provider == "gmail":
                count = sync_service.sync_gmail(account)
            elif provider == "outlook":
                count = sync_service.sync_outlook(account)
            elif provider == "google_calendar":
                count = sync_service.sync_calendar(account)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

            return {
                "status": "completed",
                "provider": provider,
                "synced_items": count,
            }
        else:
            # Sync all accounts
            results = sync_service.sync_all_accounts(str(user.id))

            total_synced = sum(v for v in results.values() if isinstance(v, int))

            return {
                "status": "completed",
                "provider": "all",
                "synced_items": total_synced,
                "details": results,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


class ResyncGmailRequest(BaseModel):
    limit: int = 100
    newer_than_days: int = 365


@router.post("/resync-gmail")
async def resync_gmail(request: ResyncGmailRequest, db: Session = Depends(get_db)):
    """
    Re-fetch existing Gmail items to backfill full HTML bodies and metadata.
    Dev/ops endpoint; not exposed in UI.
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == "gmail",
            ConnectedAccount.status == "active",
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="No active Gmail account found")

    sync_service = SyncService(db)
    try:
        updated = sync_service.resync_gmail_items(
            account,
            limit=request.limit,
            newer_than_days=request.newer_than_days,
        )
        return {
            "status": "completed",
            "updated": updated,
        }
    except Exception as e:
        logger.error(f"Gmail resync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gmail resync failed: {str(e)}")


@router.post("/refresh-inbox")
async def refresh_inbox(db: Session = Depends(get_db)):
    """
    Refresh the inbox by syncing Gmail and Outlook accounts.

    This is called by the refresh button in the UI.
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    sync_service = SyncService(db)
    results = {}
    total_synced = 0

    # Get email accounts
    accounts = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider.in_(["gmail", "outlook"]),
            ConnectedAccount.status == "active",
        )
        .all()
    )

    if not accounts:
        return {
            "status": "no_accounts",
            "message": "No email accounts connected. Go to Settings to connect Gmail or Outlook.",
            "synced_items": 0,
        }

    for account in accounts:
        try:
            if account.provider == "gmail":
                count = sync_service.sync_gmail(account)
                results["gmail"] = count
                total_synced += count
                # Emit inbox update
                if count > 0:
                    await emit_inbox_update(
                        "items_synced",
                        {
                            "provider": "gmail",
                            "count": count,
                        },
                    )
            elif account.provider == "outlook":
                count = sync_service.sync_outlook(account)
                results["outlook"] = count
                total_synced += count
                # Emit inbox update
                if count > 0:
                    await emit_inbox_update(
                        "items_synced",
                        {
                            "provider": "outlook",
                            "count": count,
                        },
                    )
        except Exception as e:
            logger.error(f"Sync failed for {account.provider}: {e}")
            results[account.provider] = f"Error: {str(e)}"

    return {
        "status": "completed",
        "synced_items": total_synced,
        "details": results,
    }


@router.post("/refresh-calendar")
async def refresh_calendar(db: Session = Depends(get_db)):
    """
    Refresh the calendar by syncing Google Calendar.

    This is called by the refresh button in the calendar UI.
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    sync_service = SyncService(db)

    # Get calendar accounts
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == "google_calendar",
            ConnectedAccount.status == "active",
        )
        .first()
    )

    if not account:
        return {
            "status": "no_accounts",
            "message": "No calendar account connected. Go to Settings to connect Google Calendar.",
            "synced_items": 0,
        }

    try:
        count = sync_service.sync_calendar(account)
        # Emit calendar update
        if count > 0:
            await emit_calendar_update(
                "events_synced",
                {
                    "count": count,
                },
            )
        return {
            "status": "completed",
            "synced_items": count,
        }
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status")
async def get_sync_status(db: Session = Depends(get_db)):
    """Get sync status for all connected accounts."""
    user = db.query(User).first()
    if not user:
        return {"accounts": []}

    accounts = (
        db.query(ConnectedAccount)
        .filter(ConnectedAccount.user_id == user.id, ConnectedAccount.status == "active")
        .all()
    )

    return {
        "accounts": [
            {
                "provider": account.provider,
                "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
                "status": account.status,
            }
            for account in accounts
        ]
    }
