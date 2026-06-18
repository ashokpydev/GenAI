# ContextOps AI Architecture

```mermaid
flowchart LR
  User["Business / Analyst / Admin"] --> UI["React Dashboard"]
  UI --> API["FastAPI API Layer"]
  API --> Auth["JWT + RBAC"]
  API --> Docs["Document Ingestion"]
  Docs --> Extract["Extract + Clean + Chunk"]
  Extract --> Embed["Local Embeddings"]
  Embed --> Store["SQL Metadata + Vector JSON"]
  API --> RAG["RAG Assistant"]
  RAG --> Store
  RAG --> Guard["Validator + Risk Score"]
  API --> SQL["Analytics Agent"]
  SQL --> SQLGuard["SELECT-only SQL Validator"]
  SQLGuard --> DemoDB["Analytics Database"]
  API --> Audit["Audit Logs + Usage"]
```

## MVP Coverage

- Authentication and role-based access control.
- Document upload, extraction, chunking, embedding, and indexed status tracking.
- Grounded chat with citations, confidence, latency, and hallucination risk.
- Safe analytics endpoint that allows only read-only SQL with row limits.
- Prompt template management for admin users.
- Audit logs, usage dashboard, and evaluation placeholder endpoints.
- React dashboard pages for all required MVP screens.

## Extension Points

- Replace the local hashing embedder with OpenAI, Gemini, Azure OpenAI, or BGE embeddings.
- Move vector storage from SQL JSON to PostgreSQL pgvector or Qdrant.
- Replace deterministic answer composition with LangChain or LangGraph LLM calls.
- Add Celery workers for background ingestion.
- Add human approval records for ticket creation and email tools.
- Add RAGAS, DeepEval, or LangSmith evaluation pipelines.
