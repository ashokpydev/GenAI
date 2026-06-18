from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_analyst_or_admin
from app.db.session import get_db
from app.models import AnalyticsHistory, User
from app.schemas.api import AnalyticsRequest, AnalyticsResponse
from app.services.analytics import run_analytics_query
from app.services.audit import write_audit


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/query", response_model=AnalyticsResponse)
def query(payload: AnalyticsRequest, db: Session = Depends(get_db), current_user: User = Depends(require_analyst_or_admin)):
    try:
        result = run_analytics_query(payload.question, payload.sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.add(AnalyticsHistory(user_id=current_user.id, question=payload.question, sql=result["sql"], summary=result["summary"]))
    db.commit()
    write_audit(db, action="analytics.query", user=current_user, resource_type="analytics", details={"sql": result["sql"]})
    return result


@router.get("/history")
def history(db: Session = Depends(get_db), current_user: User = Depends(require_analyst_or_admin)):
    return db.query(AnalyticsHistory).order_by(AnalyticsHistory.created_at.desc()).limit(50).all()
