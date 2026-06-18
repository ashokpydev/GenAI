from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Document, User
from app.schemas.api import DocumentRead
from app.services.audit import write_audit
from app.services.document_ingestion import index_document


router = APIRouter(prefix="/documents", tags=["documents"])


def index_document_by_id(document_id: int) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document:
            index_document(db, document)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentRead)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "document.txt").name
    path = settings.upload_dir / f"{uuid4().hex}_{safe_name}"
    path.write_bytes(file.file.read())
    document = Document(
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        owner_id=current_user.id,
        source_path=str(path),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    if settings.use_background_indexing:
        background_tasks.add_task(index_document_by_id, document.id)
        indexed = document
    else:
        indexed = index_document(db, document)
    write_audit(
        db,
        action="document.uploaded",
        user=current_user,
        resource_type="document",
        resource_id=str(document.id),
        details={"status": indexed.status.value, "filename": safe_name},
    )
    return indexed


@router.post("/{document_id}/index", response_model=DocumentRead)
def reindex_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None or (current_user.role.value != "admin" and document.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Document not found.")
    indexed = index_document(db, document)
    write_audit(db, action="document.reindexed", user=current_user, resource_type="document", resource_id=str(document_id))
    return indexed


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Document)
    if current_user.role.value != "admin":
        query = query.filter(Document.owner_id == current_user.id)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None or (current_user.role.value != "admin" and document.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None or (current_user.role.value != "admin" and document.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(document)
    db.commit()
    write_audit(db, action="document.deleted", user=current_user, resource_type="document", resource_id=str(document_id))
    return {"ok": True}
