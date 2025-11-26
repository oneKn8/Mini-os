"""
User preferences API routes.
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import User, UserPreferences
import uuid

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferencesUpdate(BaseModel):
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    ai_provider: Optional[str] = None
    auto_sync_interval: Optional[str] = None


@router.get("")
async def get_preferences(db: Session = Depends(get_db)):
    """Get user preferences."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()

    if not prefs:
        # Create default preferences
        prefs = UserPreferences(
            user_id=user.id,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return {
        "quiet_hours_enabled": bool(prefs.quiet_hours_start and prefs.quiet_hours_end),
        "quiet_hours_start": prefs.quiet_hours_start or "22:00",
        "quiet_hours_end": prefs.quiet_hours_end or "08:00",
        "timezone": user.timezone or "UTC",
        "location_city": user.location_city,
        "location_country": user.location_country,
        "ai_provider": os.getenv("AI_PROVIDER", "openai"),
        "auto_sync_interval": "manual",  # TODO: Store in preferences
    }


@router.put("")
async def update_preferences(update: PreferencesUpdate, db: Session = Depends(get_db)):
    """Update user preferences."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()

    if not prefs:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)

    if update.quiet_hours_enabled is not None:
        if update.quiet_hours_enabled:
            prefs.quiet_hours_start = update.quiet_hours_start or "22:00"
            prefs.quiet_hours_end = update.quiet_hours_end or "08:00"
        else:
            prefs.quiet_hours_start = None
            prefs.quiet_hours_end = None

    if update.timezone:
        user.timezone = update.timezone

    if update.location_city:
        user.location_city = update.location_city

    if update.location_country:
        user.location_country = update.location_country

    # TODO: Store AI provider and sync interval in preferences
    if update.ai_provider:
        # For now, this would require updating .env or a config system
        pass

    db.commit()

    return {"status": "updated"}
