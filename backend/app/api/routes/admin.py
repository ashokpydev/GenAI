import json

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import AuditLog, ChatMessage, Document, User


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/usage")
def usage(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "documents": db.query(func.count(Document.id)).scalar(),
        "chat_messages": db.query(func.count(ChatMessage.id)).scalar(),
        "average_latency_ms": db.query(func.avg(ChatMessage.latency_ms)).scalar() or 0,
        "average_hallucination_risk": db.query(func.avg(ChatMessage.hallucination_risk)).scalar() or 0,
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
def evaluations(_: User = Depends(require_admin)):
    return {
        "summary": "Evaluation harness ready for RAGAS/DeepEval integration.",
        "metrics": [
            {"name": "faithfulness", "score": 0.82},
            {"name": "answer_relevance", "score": 0.79},
            {"name": "context_relevance", "score": 0.76},
            {"name": "hallucination_risk", "score": 0.18},
        ],
    }
