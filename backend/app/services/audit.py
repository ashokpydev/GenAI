import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def write_audit(
    db: Session,
    *,
    action: str,
    user: User | None = None,
    resource_type: str = "",
    resource_id: str = "",
    details: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details or {}),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
