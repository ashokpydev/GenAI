from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.api import ToolRunRequest
from app.services.tools import list_tools, run_tool


router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
def tools(_: User = Depends(get_current_user)):
    return list_tools()


@router.post("/run")
def execute_tool(payload: ToolRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return run_tool(db, current_user, payload.tool_name, payload.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
