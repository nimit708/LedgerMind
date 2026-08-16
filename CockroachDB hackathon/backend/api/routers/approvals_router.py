"""Approvals router — pending agent decisions from CockroachDB."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from ..auth import CurrentUser, get_current_user
from ..database import async_session

router = APIRouter()


@router.get("/stats")
async def get_approval_stats(user: CurrentUser = Depends(get_current_user)):
    """Get approval stats — pending, approved today, rejected today."""
    try:
        async with async_session() as session:
            r = await session.execute(text(
                "SELECT "
                "COUNT(*) FILTER (WHERE approval_status = 'pending') as pending, "
                "COUNT(*) FILTER (WHERE approval_status = 'approved' AND approved_at > now() - interval '24 hours') as approved_today, "
                "COUNT(*) FILTER (WHERE approval_status = 'rejected' AND approved_at > now() - interval '24 hours') as rejected_today "
                "FROM agent_decisions"
            ))
            row = r.fetchone()
            return {
                "pending": row[0],
                "approved_today": row[1],
                "rejected_today": row[2],
            }
    except Exception as e:
        return {"pending": 0, "approved_today": 0, "rejected_today": 0, "_db_error": str(e)}


@router.get("/pending")
async def get_pending_approvals(user: CurrentUser = Depends(get_current_user)):
    try:
        async with async_session() as session:
            r = await session.execute(text(
                "SELECT id, task_type, observation, analysis, recommendation, confidence, risk_level, created_at "
                "FROM agent_decisions WHERE approval_status = 'pending' ORDER BY created_at DESC"
            ))
            approvals = [
                {
                    "id": str(row[0]),
                    "task_type": row[1],
                    "summary": row[2][:100],
                    "explanation": row[3],
                    "proposed_action": row[4],
                    "confidence": row[5],
                    "risk_level": row[6],
                    "created_at": row[7].isoformat(),
                }
                for row in r.fetchall()
            ]
            return {"approvals": approvals}
    except Exception as e:
        return {"approvals": [], "_db_error": str(e)}


class DecisionRequest(BaseModel):
    status: str
    reason: str = None


@router.post("/{approval_id}/decide")
async def decide_approval(approval_id: str, request: DecisionRequest, user: CurrentUser = Depends(get_current_user)):
    try:
        async with async_session() as session:
            await session.execute(text(
                "UPDATE agent_decisions SET approval_status = :status, approved_at = now() WHERE id = :id"
            ), {"status": request.status, "id": approval_id})
            await session.commit()
            return {"status": "ok", "approval_id": approval_id, "decision": request.status}
    except Exception as e:
        return {"status": "error", "message": str(e)}
