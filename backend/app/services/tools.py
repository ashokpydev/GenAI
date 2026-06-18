import json
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ApprovalRequest, ApprovalStatus, ToolExecution, User
from app.services.audit import write_audit


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    sensitive: bool
    handler: ToolHandler


def calculator(payload: dict[str, Any]) -> dict[str, Any]:
    expression = str(payload.get("expression", ""))
    if not expression or any(token in expression for token in ["__", "import", "open", "exec", "eval"]):
        raise ValueError("Unsafe calculator expression.")
    result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307 - constrained arithmetic sandbox
    return {"result": result}


def report_generator(payload: dict[str, Any]) -> dict[str, Any]:
    title = payload.get("title", "ContextOps Report")
    sections = payload.get("sections", [])
    body = "\n\n".join(f"## {section.get('title', 'Section')}\n{section.get('content', '')}" for section in sections)
    return {"title": title, "markdown": f"# {title}\n\n{body}".strip()}


def ticket_creator(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": "DRAFT-TICKET",
        "status": "draft_pending_external_connector",
        "summary": payload.get("summary", ""),
    }


def email_draft(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "to": payload.get("to", ""),
        "subject": payload.get("subject", ""),
        "body": payload.get("body", ""),
        "status": "draft",
    }


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "calculator": ToolSpec("calculator", "Evaluate constrained arithmetic expressions.", False, calculator),
    "report_generator": ToolSpec("report_generator", "Generate a markdown report draft.", True, report_generator),
    "ticket_creator": ToolSpec("ticket_creator", "Create a draft support ticket.", True, ticket_creator),
    "email_draft": ToolSpec("email_draft", "Draft an email for human review.", True, email_draft),
}


def list_tools() -> list[dict[str, Any]]:
    sensitive_from_config = set(get_settings().sensitive_tool_names.split(","))
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "sensitive": spec.sensitive or spec.name in sensitive_from_config,
        }
        for spec in TOOL_REGISTRY.values()
    ]


def run_tool(db: Session, user: User, tool_name: str, payload: dict[str, Any], approved: bool = False) -> dict[str, Any]:
    if tool_name not in TOOL_REGISTRY:
        raise ValueError("Unknown tool.")
    spec = TOOL_REGISTRY[tool_name]
    sensitive = spec.sensitive or tool_name in set(get_settings().sensitive_tool_names.split(","))
    if sensitive and not approved:
        request = ApprovalRequest(
            requester_id=user.id,
            tool_name=tool_name,
            payload_json=json.dumps(payload),
            reason="Sensitive tool execution requires human approval.",
            status=ApprovalStatus.pending,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        write_audit(db, action="approval.requested", user=user, resource_type="approval", resource_id=str(request.id))
        return {"status": "approval_required", "approval_request_id": request.id}

    output = spec.handler(payload)
    execution = ToolExecution(
        user_id=user.id,
        tool_name=tool_name,
        input_json=json.dumps(payload),
        output_json=json.dumps(output),
        requires_approval=sensitive,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    write_audit(db, action="tool.executed", user=user, resource_type="tool", resource_id=str(execution.id), details={"tool": tool_name})
    return {"status": "completed", "execution_id": execution.id, "output": output}
