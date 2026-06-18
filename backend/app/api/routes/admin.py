import json

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import ApprovalRequest, ApprovalStatus, AuditLog, ChatMessage, Document, EvaluationRun, ToolExecution, User, UserRole


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/usage")
def usage(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "documents": db.query(func.count(Document.id)).scalar(),
        "chat_messages": db.query(func.count(ChatMessage.id)).scalar(),
        "average_latency_ms": db.query(func.avg(ChatMessage.latency_ms)).scalar() or 0,
        "average_hallucination_risk": db.query(func.avg(ChatMessage.hallucination_risk)).scalar() or 0,
        "prompt_tokens": db.query(func.sum(ChatMessage.prompt_tokens)).scalar() or 0,
        "completion_tokens": db.query(func.sum(ChatMessage.completion_tokens)).scalar() or 0,
        "cost_usd": db.query(func.sum(ChatMessage.cost_usd)).scalar() or 0,
        "tool_executions": db.query(func.count(ToolExecution.id)).scalar(),
        "pending_approvals": db.query(func.count(ApprovalRequest.id)).filter(ApprovalRequest.status == ApprovalStatus.pending).scalar(),
    }


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [
        {
            "id": entry.id,
            "user_id": entry.user_id,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "details": json.loads(entry.details_json),
            "created_at": entry.created_at,
        }
        for entry in entries
    ]


@router.get("/evaluations")
def evaluations(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    latest_run = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).first()
    if latest_run:
        metrics = json.loads(latest_run.metrics_json)
        return {
            "summary": f"Latest evaluation run {latest_run.id} completed with {metrics.get('cases', 0)} cases.",
            "metrics": [{"name": key, "score": value} for key, value in metrics.items() if key != "cases"],
        }
    return {
        "summary": "Evaluation harness ready. Add cases and run evaluations to populate metrics.",
        "metrics": [
            {"name": "faithfulness", "score": 0.0},
            {"name": "answer_relevance", "score": 0.0},
            {"name": "context_relevance", "score": 0.0},
            {"name": "hallucination_risk", "score": 0.0},
        ],
    }


@router.get("/users")
def users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found.")
    if "role" in payload:
        user.role = UserRole(payload["role"])
    if "is_active" in payload:
        user.is_active = bool(payload["is_active"])
    db.commit()
    db.refresh(user)
    return user
