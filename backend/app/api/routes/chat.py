import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ChatMessage, User
from app.schemas.api import ChatRequest, ChatResponse
from app.services.audit import write_audit
from app.services.rag import answer_question


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = answer_question(db, current_user, payload.question, payload.conversation_id)
    write_audit(
        db,
        action="chat.answered",
        user=current_user,
        resource_type="conversation",
        resource_id=str(result["conversation_id"]),
        details={"confidence_score": result["confidence_score"], "hallucination_risk": result["hallucination_risk"]},
    )
    return result


@router.get("/history")
def chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "sources": json.loads(message.sources_json),
            "created_at": message.created_at,
        }
        for message in messages
    ]


@router.get("/{conversation_id}")
def conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages
