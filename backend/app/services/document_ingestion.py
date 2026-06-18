import csv
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk, DocumentStatus, User, UserRole
from app.services.vector_store import mirror_chunks_to_vector_store, query_vector_store


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


def lexical_score(query: str, text: str) -> float:
    query_terms = WORD_RE.findall(query.lower())
    if not query_terms:
        return 0.0
    text_terms = WORD_RE.findall(text.lower())
    if not text_terms:
        return 0.0
    text_counts: dict[str, int] = {}
    for term in text_terms:
        text_counts[term] = text_counts.get(term, 0) + 1
    matched = sum(min(3, text_counts.get(term, 0)) for term in query_terms)
    return min(1.0, matched / max(1, len(query_terms)))


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
    if suffix == ".docx":
        return extract_openxml_text(path, ("word/document.xml",))
    if suffix == ".pptx":
        with zipfile.ZipFile(path) as archive:
            slide_names = sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
        return extract_openxml_text(path, tuple(slide_names))
    if suffix == ".xlsx":
        with zipfile.ZipFile(path) as archive:
            sheet_names = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
            shared_strings = extract_shared_strings(archive)
            values: list[str] = []
            for sheet_name in sheet_names:
                root = ElementTree.fromstring(archive.read(sheet_name))
                for cell in root.iter():
                    if cell.tag.endswith("}c"):
                        cell_type = cell.attrib.get("t")
                        value = next((child.text for child in cell if child.tag.endswith("}v")), "")
                        if value and cell_type == "s":
                            value = shared_strings[int(value)]
                        if value:
                            values.append(value)
            return "\n".join(values)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_openxml_text(path: Path, member_names: tuple[str, ...]) -> str:
    values: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for member_name in member_names:
            if member_name not in archive.namelist():
                continue
            root = ElementTree.fromstring(archive.read(member_name))
            values.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
    return "\n".join(value for value in values if value.strip())


def extract_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root:
        parts = [node.text or "" for node in item.iter() if node.tag.endswith("}t")]
        values.append("".join(parts))
    return values


def index_document(db: Session, document: Document) -> Document:
    document.status = DocumentStatus.processing
    db.commit()
    try:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        db.commit()
        text = clean_text(extract_text(Path(document.source_path), document.content_type))
        chunks = split_text(text)
        created_chunks: list[DocumentChunk] = []
        embeddings: list[list[float]] = []
        for index, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk,
                embedding=json.dumps(embedding),
            )
            db.add(document_chunk)
            db.flush()
            created_chunks.append(document_chunk)
            embeddings.append(embedding)
        mirror_chunks_to_vector_store(created_chunks, embeddings)
        document.status = DocumentStatus.indexed
        document.error_message = None
    except Exception as exc:  # pragma: no cover - defensive status capture
        document.status = DocumentStatus.failed
        document.error_message = str(exc)
    db.commit()
    db.refresh(document)
    return document


def search_chunks(db: Session, query: str, top_k: int | None = None, user: User | None = None) -> list[tuple[DocumentChunk, float]]:
    settings = get_settings()
    limit = top_k or settings.top_k
    query_vector = embed_text(query)
    scored: list[tuple[DocumentChunk, float]] = []
    chroma_ids = query_vector_store(query_vector, limit * 3)
    chunk_query = db.query(DocumentChunk).join(Document).filter(Document.status == DocumentStatus.indexed)
    if chroma_ids:
        chunk_query = chunk_query.filter(DocumentChunk.id.in_(chroma_ids))
    if user and user.role not in {UserRole.admin, UserRole.compliance_user}:
        chunk_query = chunk_query.filter(Document.owner_id == user.id)
    for chunk in chunk_query.all():
        vector_score = cosine_similarity(query_vector, json.loads(chunk.embedding))
        keyword_score = lexical_score(query, chunk.text)
        scored.append((chunk, round((0.72 * vector_score) + (0.28 * keyword_score), 6)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
