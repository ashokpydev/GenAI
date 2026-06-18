import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import EvaluationCase, EvaluationRun, User
from app.schemas.api import EvaluationCaseCreate
from app.services.evaluation import add_evaluation_case, run_evaluations


router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/cases")
def create_case(payload: EvaluationCaseCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return add_evaluation_case(db, current_user, payload.question, payload.expected_answer, payload.required_source)


@router.get("/cases")
def list_cases(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(EvaluationCase).order_by(EvaluationCase.created_at.desc()).all()


@router.post("/run")
def run_eval(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    run = run_evaluations(db, current_user)
    return {"id": run.id, "status": run.status.value, "metrics": json.loads(run.metrics_json)}


@router.get("/runs")
def list_runs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(20).all()
    return [{"id": run.id, "status": run.status.value, "metrics": json.loads(run.metrics_json), "created_at": run.created_at} for run in runs]
