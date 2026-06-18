from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import PromptTemplate, User, UserRole
from app.services.analytics import ensure_demo_analytics_db


def seed_db(db: Session) -> None:
    if not db.query(User).filter(User.email == "admin@contextops.ai").first():
        admin = User(
            email="admin@contextops.ai",
            full_name="ContextOps Admin",
            role=UserRole.admin,
            hashed_password=hash_password("Admin@12345"),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        db.add_all(
            [
                PromptTemplate(
                    name="rag_answer",
                    version="1.0.0",
                    description="Grounded answer prompt with citation requirement.",
                    template="Answer only from context. If context is missing, say you do not know. Include citations.",
                    input_variables='["question", "context"]',
                    created_by_id=admin.id,
                ),
                PromptTemplate(
                    name="sql_generation",
                    version="1.0.0",
                    description="Generate safe read-only SQL for analytics.",
                    template="Create a SELECT-only query with a row limit. Never use mutating SQL.",
                    input_variables='["question", "schema"]',
                    created_by_id=admin.id,
                ),
            ]
        )
        db.commit()
    ensure_demo_analytics_db()
