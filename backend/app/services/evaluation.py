import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import EvaluationCase, EvaluationRun, EvaluationStatus, User
from app.services.guardrails import groundedness_score
from app.services.rag import answer_question


def add_evaluation_case(db: Session, user: User, question: str, expected_answer: str, required_source: str = "") -> EvaluationCase:
    case = EvaluationCase(question=question, expected_answer=expected_answer, required_source=required_source, created_by_id=user.id)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def run_evaluations(db: Session, user: User) -> EvaluationRun:
    cases = db.query(EvaluationCase).all()
    metrics = {"cases": len(cases), "faithfulness": 0.0, "answer_relevance": 0.0, "context_relevance": 0.0, "hallucination_risk": 0.0}
    if cases:
        faithfulness_scores: list[float] = []
        relevance_scores: list[float] = []
        risk_scores: list[float] = []
        for case in cases:
            result = answer_question(db, user, case.question)
            context = " ".join(source.get("excerpt", "") for source in result["sources"])
            faithfulness_scores.append(groundedness_score(result["answer"], context))
            expected_terms = {term.lower() for term in case.expected_answer.split() if len(term) > 3}
            answer_terms = {term.lower() for term in result["answer"].split() if len(term) > 3}
            relevance_scores.append(len(expected_terms & answer_terms) / max(1, len(expected_terms)))
            risk_scores.append(result["hallucination_risk"])
        metrics = {
            "cases": len(cases),
            "faithfulness": round(sum(faithfulness_scores) / len(faithfulness_scores), 4),
            "answer_relevance": round(sum(relevance_scores) / len(relevance_scores), 4),
            "context_relevance": round(sum(faithfulness_scores) / len(faithfulness_scores), 4),
            "hallucination_risk": round(sum(risk_scores) / len(risk_scores), 4),
        }
    run = EvaluationRun(
        status=EvaluationStatus.completed,
        metrics_json=json.dumps(metrics),
        created_by_id=user.id,
        completed_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
