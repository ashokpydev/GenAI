import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import PromptTemplate, User
from app.schemas.api import PromptCreate, PromptRead
from app.services.audit import write_audit


router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=PromptRead)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    prompt = PromptTemplate(
        name=payload.name,
        version=payload.version,
        description=payload.description,
        template=payload.template,
        input_variables=json.dumps(payload.input_variables),
        is_active=payload.is_active,
        created_by_id=current_user.id,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    write_audit(db, action="prompt.created", user=current_user, resource_type="prompt", resource_id=str(prompt.id))
    return prompt


@router.get("", response_model=list[PromptRead])
def list_prompts(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return db.query(PromptTemplate).order_by(PromptTemplate.created_at.desc()).all()


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(prompt_id: int, payload: PromptCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    prompt = db.get(PromptTemplate, prompt_id)
    if prompt is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Prompt not found.")
    for field, value in payload.model_dump().items():
        setattr(prompt, field, json.dumps(value) if field == "input_variables" else value)
    db.commit()
    db.refresh(prompt)
    write_audit(db, action="prompt.updated", user=current_user, resource_type="prompt", resource_id=str(prompt.id))
    return prompt
