# ContextOps AI

AI-powered enterprise knowledge, analytics, and action copilot built from the client requirement document.

## What Is Included

- FastAPI backend with JWT auth, RBAC, document upload, RAG chat, analytics, prompts, audit logs, and admin usage APIs.
- React + TypeScript frontend dashboard with all required MVP pages.
- Local deterministic embeddings for offline demos, with clear extension points for pgvector, Qdrant, OpenAI, Gemini, or Azure OpenAI.
- Safe SQL analytics agent that allows only `SELECT` queries and enforces row limits.
- Docker Compose setup, tests, architecture notes, deployment guide, demo data, and demo script.

## Quick Start

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Default admin:

- Email: `admin@contextops.ai`
- Password: `Admin@12345`

## Docker

```bash
docker compose up --build
```

## Tests

```bash
cd backend
pytest
```

## Demo

Upload `demo/documents/contextops_policy.txt`, then ask:

```text
What must happen before sensitive operations are executed?
```

For analytics, ask:

```text
What were the top products by revenue?
```

## Documents

- [Architecture](docs/architecture.md)
- [Deployment guide](docs/deployment-guide.md)
- [Client demo script](docs/demo-script.md)
