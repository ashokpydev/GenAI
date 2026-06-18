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
- Put uploads in durable object storage.
- Run document indexing in Celery with Redis.
- Put the backend behind Nginx or an API gateway.
- Send OpenTelemetry traces to the organization observability stack.
- Configure SSO/OAuth2 before enterprise rollout.
- Keep `SENSITIVE_TOOL_NAMES` aligned with the organization's approval policy.
