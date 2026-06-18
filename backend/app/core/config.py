from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContextOps AI"
    environment: str = "local"
    database_url: str = "sqlite:///./storage/contextops.db"
    analytics_database_url: str = "sqlite:///./storage/demo_analytics.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    upload_dir: Path = Path("storage/uploads")
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 5
    llm_provider: str = "ollama"
    llm_model: str = "local-grounded-synthesizer"
    llm_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    embedding_provider: str = "local"
    vector_store_provider: str = "chroma"
    chroma_path: str = "storage/chroma"
    use_background_indexing: bool = True
    monthly_budget_usd: float = 100.0
    sensitive_tool_names: str = "ticket_creator,email_draft,report_generator"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
