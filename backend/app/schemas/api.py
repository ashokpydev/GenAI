from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models import DocumentStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: UserRole = UserRole.business_user


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class DocumentRead(BaseModel):
    id: int
    filename: str
    content_type: str
    status: DocumentStatus
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str = Field(min_length=2)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: list[dict[str, Any]]
    confidence_score: float
    hallucination_risk: float
    latency_ms: int


class AnalyticsRequest(BaseModel):
    question: str
    sql: str | None = None


class AnalyticsResponse(BaseModel):
    sql: str
    rows: list[dict[str, Any]]
    summary: str


class PromptCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    template: str
    input_variables: list[str] = []
    is_active: bool = True


class PromptRead(PromptCreate):
    id: int
    input_variables: str
    created_at: datetime

    model_config = {"from_attributes": True}
