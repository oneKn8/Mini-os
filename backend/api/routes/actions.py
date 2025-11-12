"""
Actions API routes
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import ActionProposal, PreferenceSignal
from backend.executor.action_executor import ActionExecutor

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/pending")
async def get_pending_actions(db: Session = Depends(get_db)):
    """Get all pending action proposals."""
    proposals = (
        db.query(ActionProposal)
        .filter(ActionProposal.status == "pending")
        .order_by(ActionProposal.proposed_at.desc())
        .all()
    )

    return [
        {
            "id": str(p.id),
            "agent_name": p.agent_name,
            "action_type": p.action_type,
            "explanation": p.explanation,
            "risk_level": p.risk_level,
            "payload": p.payload,
            "proposed_at": p.proposed_at.isoformat(),
        }
        for p in proposals
    ]


@router.post("/{action_id}/approve")
async def approve_action(action_id: str, db: Session = Depends(get_db)):
    """Approve an action proposal and execute it."""
    proposal = db.query(ActionProposal).filter(ActionProposal.id == action_id).first()

    if not proposal:
        return {"error": "Action not found"}, 404

    if proposal.status != "pending":
        return {"error": "Action already processed"}, 400

    proposal.status = "approved"
    proposal.reviewed_at = datetime.utcnow()
    db.commit()

    executor = ActionExecutor(db)
    log = executor.execute(proposal)

    signal = PreferenceSignal(
        user_id=proposal.user_id,
        signal_type="approve_proposal",
        related_item_id=proposal.related_item_id,
        metadata={"action_id": str(action_id)},
    )
    db.add(signal)
    db.commit()

    return {"status": "approved", "execution_status": log.executor_status}


@router.post("/{action_id}/reject")
async def reject_action(action_id: str, db: Session = Depends(get_db)):
    """Reject an action proposal."""
    proposal = db.query(ActionProposal).filter(ActionProposal.id == action_id).first()

    if not proposal:
        return {"error": "Action not found"}, 404

    if proposal.status != "pending":
        return {"error": "Action already processed"}, 400

    proposal.status = "rejected"
    proposal.reviewed_at = datetime.utcnow()
    db.commit()

    signal = PreferenceSignal(
        user_id=proposal.user_id,
        signal_type="reject_proposal",
        related_item_id=proposal.related_item_id,
        metadata={"action_id": str(action_id)},
    )
    db.add(signal)
    db.commit()

    return {"status": "rejected"}
