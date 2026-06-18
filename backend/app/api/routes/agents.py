from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.api import ChatRequest
from app.services.orchestration import classify_request, run_orchestrated_request


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/route")
def route(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    decision = classify_request(payload.question)
    return {"route": decision.route, "reason": decision.reason, "user_id": current_user.id}


@router.post("/run")
def run(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return run_orchestrated_request(db, current_user, payload.question)
