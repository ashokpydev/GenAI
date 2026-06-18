# Deployment Guide

## Local Docker

```bash
docker compose up --build
```

Frontend: `http://localhost:5173`

Backend API docs: `http://localhost:8000/docs`

Default admin:

- Email: `admin@contextops.ai`
- Password: `Admin@12345`

## Production Notes

- Set a strong `SECRET_KEY`.
- Use PostgreSQL for `DATABASE_URL`.
- Use pgvector or Qdrant for vector search.
- Configure `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY` when replacing the local grounded synthesizer.
- For a fully free local LLM, install Ollama and set `LLM_PROVIDER=ollama` and `OLLAMA_MODEL=llama3.2` or another locally pulled model.
- For local open-source vector storage, install `backend/requirements-local.txt` and set `VECTOR_STORE_PROVIDER=chroma`.
- Put uploads in durable object storage.
- Run document indexing in Celery with Redis.
- Put the backend behind Nginx or an API gateway.
- Send OpenTelemetry traces to the organization observability stack.
- Configure SSO/OAuth2 before enterprise rollout.
- Keep `SENSITIVE_TOOL_NAMES` aligned with the organization's approval policy.

## Free Local Stack

Optional local-only services:

```bash
cd backend
pip install -r requirements-local.txt
ollama pull llama3.2
set LLM_PROVIDER=ollama
set OLLAMA_MODEL=llama3.2
set VECTOR_STORE_PROVIDER=chroma
uvicorn app.main:app --reload
```

Celery worker, if Redis is running:

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=INFO
```
