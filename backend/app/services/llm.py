from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    provider: str
    model: str


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class LocalGroundedLLM:
    def generate(self, *, question: str, context: str, draft_answer: str) -> LLMResult:
        settings = get_settings()
        answer = draft_answer.strip()
        if context and "Source-backed answer:" not in answer:
            answer = f"Source-backed answer: {answer}"
        prompt_tokens = estimate_tokens(question) + estimate_tokens(context)
        completion_tokens = estimate_tokens(answer)
        return LLMResult(
            text=answer,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=0.0,
            provider=settings.llm_provider,
            model=settings.llm_model,
        )


def get_llm() -> LocalGroundedLLM:
    # Production extension point: add OpenAI, Gemini, Azure OpenAI, or local model clients here.
    return LocalGroundedLLM()
