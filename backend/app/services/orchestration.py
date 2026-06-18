from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import User
from app.services.analytics import run_analytics_query
from app.services.guardrails import validate_user_input
from app.services.rag import answer_question
from app.services.tools import run_tool


@dataclass
class RouteDecision:
    route: str
    reason: str


def classify_request(text: str) -> RouteDecision:
    q = text.lower()
    guardrail = validate_user_input(text)
    if not guardrail["allowed"]:
        return RouteDecision("guardrail", "Prompt-injection pattern detected.")
    if any(term in q for term in ["revenue", "sales", "complaint", "top products", "compare month"]):
        return RouteDecision("analytics", "Structured business metric question.")
    if any(term in q for term in ["summarize", "summary", "brief"]):
        return RouteDecision("summarization", "Summary intent detected.")
    if any(term in q for term in ["create ticket", "raise ticket"]):
        return RouteDecision("action", "Ticket action requires approval.")
    if any(term in q for term in ["draft email", "send email"]):
        return RouteDecision("action", "Email action requires approval.")
    if any(term in q for term in ["report", "generate report"]):
        return RouteDecision("report", "Report generation requires controlled tooling.")
    return RouteDecision("rag", "Default source-grounded knowledge path.")


def run_orchestrated_request(db: Session, user: User, text: str) -> dict:
    decision = classify_request(text)
    if decision.route == "guardrail":
        return {"route": decision.route, "reason": decision.reason, "result": {"answer": "Request blocked by guardrails."}}
    if decision.route == "analytics":
        return {"route": decision.route, "reason": decision.reason, "result": run_analytics_query(text)}
    if decision.route in {"action", "report"}:
        if "email" in text.lower():
            tool = "email_draft"
            payload = {"subject": "ContextOps follow-up", "body": text}
        elif "ticket" in text.lower():
            tool = "ticket_creator"
            payload = {"summary": text}
        else:
            tool = "report_generator"
            payload = {"title": "ContextOps Generated Report", "sections": [{"title": "Request", "content": text}]}
        return {"route": decision.route, "reason": decision.reason, "result": run_tool(db, user, tool, payload)}
    return {"route": decision.route, "reason": decision.reason, "result": answer_question(db, user, text)}
