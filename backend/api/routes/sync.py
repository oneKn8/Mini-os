"""
Sync API routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.ingestion.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger")
async def trigger_sync(provider: str = None, db: Session = Depends(get_db)):
    """Manually trigger a sync for one or all providers."""
    sync_service = SyncService(db)

    result = await sync_service.sync_user_data(user_id="default_user", provider_filter=provider)

    return {"status": "completed", "synced_items": result.get("total_synced", 0), "provider": provider or "all"}
