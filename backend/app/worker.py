from celery import Celery

from app.core.config import get_settings
from app.services.document_ingestion import index_document


settings = get_settings()
celery_app = Celery(
    "contextops_ai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)


@celery_app.task(name="documents.index")
def index_document_task(document_id: int) -> str:
    from app.db.session import SessionLocal
    from app.models import Document

    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return "missing"
        index_document(db, document)
        return document.status.value
    finally:
        db.close()
