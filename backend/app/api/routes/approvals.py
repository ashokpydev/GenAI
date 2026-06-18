import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import ApprovalRequest, ApprovalStatus, User
from app.schemas.api import ApprovalDecisionRequest
from app.services.audit import write_audit
from app.services.tools import run_tool


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    approvals = db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(100).all()
    return [
        {
            "id": approval.id,
            "requester_id": approval.requester_id,
            "tool_name": approval.tool_name,
            "payload": json.loads(approval.payload_json),
            "reason": approval.reason,
            "status": approval.status.value,
            "decision_note": approval.decision_note,
            "created_at": approval.created_at,
            "decided_at": approval.decided_at,
        }
        for approval in approvals
    ]


@router.post("/{approval_id}/decision")
def decide_approval(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if approval.status != ApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="Approval has already been decided.")
    approval.status = ApprovalStatus(payload.status)
    approval.reviewer_id = current_user.id
    approval.decision_note = payload.decision_note
    approval.decided_at = datetime.utcnow()
    db.commit()
    write_audit(db, action=f"approval.{payload.status}", user=current_user, resource_type="approval", resource_id=str(approval.id))
    if approval.status == ApprovalStatus.approved:
        requester = db.get(User, approval.requester_id)
        if requester is None:
            raise HTTPException(status_code=404, detail="Requester not found.")
        return run_tool(db, requester, approval.tool_name, json.loads(approval.payload_json), approved=True)
    return {"status": "rejected"}
