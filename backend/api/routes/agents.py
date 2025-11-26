"""
Agents API routes
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import AgentRunLog, User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/runs")
async def get_agent_runs(
    page: int = 1,
    limit: int = 20,
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List agent runs with pagination and filtering."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        return {"items": [], "total": 0, "page": page, "limit": limit}

    query = db.query(AgentRunLog).filter(AgentRunLog.user_id == user.id)

    if agent_name:
        query = query.filter(AgentRunLog.agent_name == agent_name)

    if status:
        query = query.filter(AgentRunLog.status == status)

    total = query.count()

    runs = query.order_by(AgentRunLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [
            {
                "id": str(run.id),
                "agent_name": run.agent_name,
                "context": run.context,
                "status": run.status,
                "duration_ms": run.duration_ms,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                # Include brief summary for list view
                "input_summary": run.input_summary,
                "output_summary": run.output_summary,
            }
            for run in runs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/runs/{run_id}")
async def get_agent_run_details(run_id: str, db: Session = Depends(get_db)):
    """Get detailed agent run log."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    run = db.query(AgentRunLog).filter(AgentRunLog.id == run_id, AgentRunLog.user_id == user.id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    return {
        "id": str(run.id),
        "agent_name": run.agent_name,
        "context": run.context,
        "status": run.status,
        "duration_ms": run.duration_ms,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "input_summary": run.input_summary,
        "output_summary": run.output_summary,
    }


@router.get("/summary")
async def get_agent_summary(db: Session = Depends(get_db)):
    """Get summary statistics for agents."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        return {}

    # Total runs
    total_runs = db.query(AgentRunLog).filter(AgentRunLog.user_id == user.id).count()

    # Runs by agent
    runs_by_agent = (
        db.query(AgentRunLog.agent_name, func.count(AgentRunLog.id))
        .filter(AgentRunLog.user_id == user.id)
        .group_by(AgentRunLog.agent_name)
        .all()
    )

    # Success rate
    success_count = (
        db.query(AgentRunLog).filter(AgentRunLog.user_id == user.id, AgentRunLog.status == "success").count()
    )

    success_rate = (success_count / total_runs * 100) if total_runs > 0 else 0

    # Recent failures
    recent_failures = (
        db.query(AgentRunLog)
        .filter(AgentRunLog.user_id == user.id, AgentRunLog.status == "error")
        .order_by(AgentRunLog.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_runs": total_runs,
        "runs_by_agent": {name: count for name, count in runs_by_agent},
        "success_rate": round(success_rate, 2),
        "recent_failures": [
            {
                "id": str(run.id),
                "agent_name": run.agent_name,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in recent_failures
        ],
    }
