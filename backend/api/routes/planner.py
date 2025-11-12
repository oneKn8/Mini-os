"""
Planner API routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import Item
from orchestrator.orchestrator import Orchestrator

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("/today")
async def get_today_plan(db: Session = Depends(get_db)):
    """Generate today's plan using the Planner Agent."""
    orchestrator = Orchestrator()

    items = (
        db.query(Item).filter(Item.ingestion_status == "processed").order_by(Item.received_at.desc()).limit(50).all()
    )

    context = orchestrator.build_context(
        intent="plan_day",
        items=[
            {
                "id": str(item.id),
                "title": item.title,
                "source_type": item.source_type,
                "importance": item.importance,
                "due_datetime": item.due_datetime.isoformat() if item.due_datetime else None,
                "start_datetime": item.start_datetime.isoformat() if item.start_datetime else None,
            }
            for item in items
        ],
        user_id="default_user",
    )

    result = await orchestrator.run("plan_day", context)

    if result.status == "success" and result.results:
        planner_result = result.results.get("planner", {})
        plan_data = planner_result.get("output_summary", {})
        return plan_data

    return {"must_do_today": [], "focus_areas": [], "time_recommendations": []}
