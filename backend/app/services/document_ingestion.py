import csv
import hashlib
import json
import math
import re
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk, DocumentStatus


WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
VECTOR_SIZE = 256


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text: str) -> list[str]:
    settings = get_settings()
    if len(text) <= settings.chunk_size:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + settings.chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - settings.chunk_overlap)
    return chunks


def embed_text(text: str) -> list[float]:
    vector = [0.0] * VECTOR_SIZE
    for token in WORD_RE.findall(text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % VECTOR_SIZE
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def extract_text(path: Path, content_type: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            rows = csv.reader(handle)
            return "\n".join(" | ".join(row) for row in rows)
    return path.read_text(encoding="utf-8", errors="ignore")


def index_document(db: Session, document: Document) -> Document:
    document.status = DocumentStatus.processing
    db.commit()
    try:
        text = clean_text(extract_text(Path(document.source_path), document.content_type))
        chunks = split_text(text)
        for index, chunk in enumerate(chunks):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    text=chunk,
                    embedding=json.dumps(embed_text(chunk)),
                )
            )
        document.status = DocumentStatus.indexed
        document.error_message = None
    except Exception as exc:  # pragma: no cover - defensive status capture
        document.status = DocumentStatus.failed
        document.error_message = str(exc)
    db.commit()
    db.refresh(document)
    return document


def search_chunks(db: Session, query: str, top_k: int | None = None) -> list[tuple[DocumentChunk, float]]:
    settings = get_settings()
    query_vector = embed_text(query)
    scored: list[tuple[DocumentChunk, float]] = []
    for chunk in db.query(DocumentChunk).join(Document).filter(Document.status == DocumentStatus.indexed).all():
        scored.append((chunk, cosine_similarity(query_vector, json.loads(chunk.embedding))))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[: top_k or settings.top_k]
