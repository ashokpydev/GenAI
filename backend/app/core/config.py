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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
