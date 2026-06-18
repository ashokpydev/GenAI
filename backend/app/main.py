from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, agents, analytics, approvals, auth, chat, documents, evaluations, prompts, tools
from app.db.init_db import seed_db
from app.db.session import Base, SessionLocal, engine


def create_app() -> FastAPI:
    app = FastAPI(title="ContextOps AI", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(analytics.router)
    app.include_router(prompts.router)
    app.include_router(tools.router)
    app.include_router(approvals.router)
    app.include_router(evaluations.router)
    app.include_router(admin.router)

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_db(db)
        finally:
            db.close()

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "ContextOps AI"}

    return app


app = create_app()
