from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.models import DocumentChunk


@lru_cache
def chroma_collection() -> Any | None:
    settings = get_settings()
    if settings.vector_store_provider.lower() != "chroma":
        return None
    try:
        import chromadb
    except ImportError:
        return None
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection("contextops_chunks")


def mirror_chunks_to_vector_store(chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
    collection = chroma_collection()
    if collection is None or not chunks:
        return
    collection.upsert(
        ids=[str(chunk.id) for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk.text for chunk in chunks],
        metadatas=[
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )


def query_vector_store(query_embedding: list[float], top_k: int) -> list[int]:
    collection = chroma_collection()
    if collection is None:
        return []
    result = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    ids = result.get("ids", [[]])[0]
    return [int(item) for item in ids]
