import re


INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|above) instructions", re.I),
    re.compile(r"reveal (the )?(system|developer) prompt", re.I),
    re.compile(r"act as (an )?unrestricted", re.I),
    re.compile(r"bypass (policy|guardrails|security)", re.I),
]

PII_PATTERNS = [
    (re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[masked-email]"),
    (re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"), "[masked-phone]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[masked-ssn]"),
]


def detect_prompt_injection(text: str) -> list[str]:
    return [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]


def mask_pii(text: str) -> str:
    masked = text
    for pattern, replacement in PII_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def validate_user_input(text: str) -> dict:
    flags = detect_prompt_injection(text)
    return {"allowed": not flags, "flags": flags, "sanitized_text": mask_pii(text)}


def groundedness_score(answer: str, context: str) -> float:
    answer_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_]{4,}", answer)}
    context_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_]{4,}", context)}
    if not answer_terms:
        return 0.0
    return round(len(answer_terms & context_terms) / len(answer_terms), 4)
