from dataclasses import dataclass
import json
from urllib import request
from urllib.error import URLError

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


class OllamaLLM(LocalGroundedLLM):
    def generate(self, *, question: str, context: str, draft_answer: str) -> LLMResult:
        settings = get_settings()
        prompt = (
            "You are ContextOps AI. Answer only from the provided enterprise context. "
            "If the context is insufficient, say you do not know. Include concise wording.\n\n"
            f"Context:\n{context[:6000]}\n\nQuestion:\n{question}\n\nDraft grounded answer:\n{draft_answer}"
        )
        payload = json.dumps({"model": settings.ollama_model, "prompt": prompt, "stream": False}).encode("utf-8")
        api_request = request.Request(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(api_request, timeout=30) as response:  # noqa: S310 - local configurable endpoint
                data = json.loads(response.read().decode("utf-8"))
            text = data.get("response") or draft_answer
            prompt_tokens = int(data.get("prompt_eval_count") or estimate_tokens(prompt))
            completion_tokens = int(data.get("eval_count") or estimate_tokens(text))
            return LLMResult(
                text=text.strip(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=0.0,
                provider="ollama",
                model=settings.ollama_model,
            )
        except (TimeoutError, URLError, OSError, json.JSONDecodeError):
            return super().generate(question=question, context=context, draft_answer=draft_answer)


def get_llm() -> LocalGroundedLLM:
    settings = get_settings()
    if settings.llm_provider.lower() == "ollama":
        return OllamaLLM()
    return LocalGroundedLLM()
