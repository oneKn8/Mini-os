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

    # Query items with their agent metadata
    items = (
        db.query(Item)
        .filter(Item.is_archived.is_(False))
        .order_by(Item.received_datetime.desc().nullsfirst())
        .limit(50)
        .all()
    )

    # Build item list for orchestrator
    item_list = []
    for item in items:
        metadata = item.agent_metadata
        item_list.append(
            {
                "id": str(item.id),
                "title": item.title or "",
                "source_type": item.source_type,
                "importance": metadata.importance if metadata else "medium",
                "due_datetime": metadata.due_datetime.isoformat() if (metadata and metadata.due_datetime) else None,
                "start_datetime": item.start_datetime.isoformat() if item.start_datetime else None,
            }
        )

    context = orchestrator.build_context(
        intent="plan_day",
        items=item_list,
        user_id="default_user",
    )

    result = await orchestrator.run("plan_day", context)

    if result.status == "success" and result.results:
        planner_result = result.results.get("planner")
        if planner_result:
            plan_data = planner_result.output_summary or {}
            return plan_data

    return {"must_do_today": [], "focus_areas": [], "time_recommendations": []}
