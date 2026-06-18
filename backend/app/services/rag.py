import json
import time

from sqlalchemy.orm import Session

from app.models import ChatMessage, Conversation, User
from app.services.document_ingestion import search_chunks
from app.services.guardrails import groundedness_score, validate_user_input
from app.services.llm import get_llm


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
    guardrail = validate_user_input(question)
    sanitized_question = guardrail["sanitized_text"]
    if conversation_id is None:
        conversation = Conversation(user_id=user.id, title=sanitized_question[:80])
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

    db.add(ChatMessage(conversation_id=conversation.id, user_id=user.id, role="user", content=sanitized_question))

    if not guardrail["allowed"]:
        answer = "I cannot process that request because it appears to contain prompt-injection instructions."
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        message = ChatMessage(
            conversation_id=conversation.id,
            user_id=user.id,
            role="assistant",
            content=answer,
            sources_json="[]",
            confidence_score=0.0,
            hallucination_risk=1.0,
            latency_ms=latency_ms,
            prompt_tokens=len(sanitized_question.split()),
            completion_tokens=len(answer.split()),
            cost_usd=0.0,
        )
        db.add(message)
        db.commit()
        return {
            "conversation_id": conversation.id,
            "answer": answer,
            "sources": [],
            "confidence_score": 0.0,
            "hallucination_risk": 1.0,
            "latency_ms": latency_ms,
            "prompt_tokens": message.prompt_tokens,
            "completion_tokens": message.completion_tokens,
            "cost_usd": 0.0,
            "guardrail_flags": guardrail["flags"],
        }

    matches = search_chunks(db, sanitized_question)
    usable_matches = [(chunk, score) for chunk, score in matches if score > 0.06]

    if not usable_matches:
        answer = "I don't know based on the approved knowledge sources available to me."
        citations: list[dict] = []
        prompt_tokens = len(sanitized_question.split())
        completion_tokens = len(answer.split())
        cost_usd = 0.0
        confidence = 0.0
        risk = 1.0
    else:
        context_text = "\n\n".join(chunk.text for chunk, _ in usable_matches)
        draft_answer = _sentence_answer(sanitized_question, [chunk.text for chunk, _ in usable_matches])
        llm_result = get_llm().generate(question=sanitized_question, context=context_text, draft_answer=draft_answer)
        answer = llm_result.text
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
        retrieval_confidence = sum(score for _, score in usable_matches) / len(usable_matches)
        groundedness = groundedness_score(answer, context_text)
        confidence = round((retrieval_confidence + groundedness) / 2, 4)
        risk = round(max(0.0, 1.0 - confidence), 4)
        prompt_tokens = llm_result.prompt_tokens
        completion_tokens = llm_result.completion_tokens
        cost_usd = llm_result.cost_usd

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
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
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
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "guardrail_flags": guardrail["flags"],
    }
