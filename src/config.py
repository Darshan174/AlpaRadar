from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Crustdata
    crustdata_api_key: str = ""
    crustdata_base_url: str = "https://api.crustdata.com"
    crustdata_api_version: str = "2025-11-01"

    # LLM — Groq free tier
    groq_api_key: str = ""
    llm_model: str = "groq/llama-3.3-70b-versatile"
    llm_fallback_model: str = "groq/llama-3.1-8b-instant"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # Alerts
    slack_bot_token: str = ""
    slack_channel: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # API
    api_secret_key: str = "change-me-in-production"
    allowed_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 60

    # Embeddings (local via fastembed)
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Logging
    log_level: str = "INFO"

    # Scheduler
    ingestion_interval_hours: int = 6

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
