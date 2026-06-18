import json
import time

from sqlalchemy.orm import Session

from app.models import ChatMessage, Conversation, User
from app.services.document_ingestion import search_chunks


def _sentence_answer(question: str, contexts: list[str]) -> str:
    terms = {term.lower() for term in question.replace("?", " ").split() if len(term) > 3}
    selected: list[str] = []
    for context in contexts:
        sentences = [part.strip() for part in context.replace("\n", " ").split(".") if part.strip()]
        for sentence in sentences:
            if any(term in sentence.lower() for term in terms):
                selected.append(sentence)
            if len(selected) >= 4:
                break
        if len(selected) >= 4:
            break
    if not selected:
        selected = [contexts[0][:450]]
    return " ".join(selected)[:1400]


def answer_question(db: Session, user: User, question: str, conversation_id: int | None = None) -> dict:
    started_at = time.perf_counter()
    if conversation_id is None:
        conversation = Conversation(user_id=user.id, title=question[:80])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    else:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user.id:
            conversation = Conversation(user_id=user.id, title=question[:80])
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

    db.add(ChatMessage(conversation_id=conversation.id, user_id=user.id, role="user", content=question))
    matches = search_chunks(db, question)
    usable_matches = [(chunk, score) for chunk, score in matches if score > 0.06]

    if not usable_matches:
        answer = "I don't know based on the approved knowledge sources available to me."
        citations: list[dict] = []
        confidence = 0.0
        risk = 1.0
    else:
        answer = _sentence_answer(question, [chunk.text for chunk, _ in usable_matches])
        citations = [
            {
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "score": round(score, 4),
                "excerpt": chunk.text[:240],
            }
            for chunk, score in usable_matches
        ]
        confidence = round(sum(score for _, score in usable_matches) / len(usable_matches), 4)
        risk = round(max(0.0, 1.0 - confidence), 4)

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    message = ChatMessage(
        conversation_id=conversation.id,
        user_id=user.id,
        role="assistant",
        content=answer,
        sources_json=json.dumps(citations),
        confidence_score=confidence,
        hallucination_risk=risk,
        latency_ms=latency_ms,
    )
    db.add(message)
    db.commit()

    return {
        "conversation_id": conversation.id,
        "answer": answer,
        "sources": citations,
        "confidence_score": confidence,
        "hallucination_risk": risk,
        "latency_ms": latency_ms,
    }
