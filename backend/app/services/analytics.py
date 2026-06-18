import re
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


BLOCKED_SQL = re.compile(r"\b(delete|update|insert|drop|alter|truncate|create|attach|pragma|replace)\b", re.I)
SENSITIVE_COLUMNS = {"email", "phone", "ssn", "password", "token"}


@lru_cache
def analytics_engine(url: str) -> Engine:
    if url in {"sqlite://", "sqlite:///:memory:"}:
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    if url.startswith("sqlite:///"):
        Path(url.replace("sqlite:///", "")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url)


def ensure_demo_analytics_db() -> None:
    settings = get_settings()
    if not settings.analytics_database_url.startswith("sqlite"):
        return
    engine = analytics_engine(settings.analytics_database_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY,
                    product TEXT NOT NULL,
                    region TEXT NOT NULL,
                    month TEXT NOT NULL,
                    revenue REAL NOT NULL,
                    complaints INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )
        count = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar_one()
        if count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO sales(product, region, month, revenue, complaints) VALUES
                    ('Knowledge Hub', 'North', '2026-05', 120000, 4),
                    ('Knowledge Hub', 'South', '2026-06', 98000, 7),
                    ('Analytics Pro', 'North', '2026-06', 142000, 3),
                    ('Analytics Pro', 'West', '2026-05', 151000, 2),
                    ('Action Desk', 'South', '2026-06', 87000, 9),
                    ('Action Desk', 'East', '2026-05', 73000, 6)
                    """
                )
            )


def question_to_sql(question: str) -> str:
    q = question.lower()
    if "complaint" in q:
        return "SELECT product, region, SUM(complaints) AS complaints FROM sales GROUP BY product, region ORDER BY complaints DESC LIMIT 10"
    if "compare" in q or "month" in q:
        return "SELECT month, product, SUM(revenue) AS revenue FROM sales GROUP BY month, product ORDER BY month DESC, revenue DESC LIMIT 20"
    if "top" in q or "revenue" in q or "sales" in q:
        return "SELECT product, SUM(revenue) AS revenue FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 5"
    return "SELECT product, region, month, revenue, complaints FROM sales LIMIT 10"


def validate_sql(sql: str) -> str:
    stripped = sql.strip().rstrip(";")
    if not stripped.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    if BLOCKED_SQL.search(stripped):
        raise ValueError("Unsafe SQL keyword detected.")
    for column in SENSITIVE_COLUMNS:
        if re.search(rf"\b{column}\b", stripped, re.I):
            raise ValueError(f"Sensitive column is not allowed: {column}")
    if " limit " not in f" {stripped.lower()} ":
        stripped = f"{stripped} LIMIT 100"
    return stripped


def run_analytics_query(question: str, sql: str | None = None) -> dict:
    ensure_demo_analytics_db()
    safe_sql = validate_sql(sql or question_to_sql(question))
    engine = analytics_engine(get_settings().analytics_database_url)
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(text(safe_sql)).fetchall()]
    summary = summarize_rows(question, rows)
    return {"sql": safe_sql, "rows": rows, "summary": summary}


def summarize_rows(question: str, rows: list[dict]) -> str:
    if not rows:
        return "No matching records were found for this analytics question."
    if "revenue" in rows[0]:
        best = max(rows, key=lambda row: float(row.get("revenue") or 0))
        return f"The strongest revenue result is {best.get('product', best.get('month'))} with {best.get('revenue')} in the current result set."
    if "complaints" in rows[0]:
        worst = max(rows, key=lambda row: int(row.get("complaints") or 0))
        return f"The highest complaint concentration is {worst.get('product')} in {worst.get('region')} with {worst.get('complaints')} complaints."
    return f"Returned {len(rows)} rows. Review the table for the detailed breakdown."
