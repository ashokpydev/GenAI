import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ANALYTICS_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "storage/test-uploads"

from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app):
        pass


def login() -> str:
    response = client.post("/auth/login", json={"email": "admin@contextops.ai", "password": "Admin@12345"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_grounded_chat():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    document = b"ContextOps AI must answer questions from company documents and include source citations."
    upload = client.post(
        "/documents/upload",
        headers=headers,
        files={"file": ("requirement.txt", document, "text/plain")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["status"] == "indexed"

    chat = client.post("/chat", headers=headers, json={"question": "What must ContextOps AI include?"})
    assert chat.status_code == 200, chat.text
    payload = chat.json()
    assert payload["sources"]
    assert "citations" in payload["answer"].lower() or "source" in payload["sources"][0]["excerpt"].lower()


def test_analytics_blocks_unsafe_sql():
    token = login()
    response = client.post(
        "/analytics/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "bad", "sql": "DROP TABLE sales"},
    )
    assert response.status_code == 400
