"""Central configuration. ALL environment variables live here (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    DATABASE_URL: str = "postgresql+psycopg://setu:setu@db:5432/setu"
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000"
    SECRET_KEY: str = "dev-only"
    LOG_LEVEL: str = "info"

    # --- Upload / storage ---
    MAX_UPLOAD_MB: int = 15
    STORAGE_PATH: str = "/data/uploads"

    # --- Memory / reducer ---
    CONFIDENCE_THRESHOLD: float = 0.7

    # --- Sharing ---
    SHARE_BASE_URL: str = "http://localhost:3000/share"

    # --- AI providers ---
    EXTRACTION_PROVIDER: str = "mock"  # mock|qwen|cloud
    QWEN_ENDPOINT: str = "http://models:8001/v1"
    REASONING_PROVIDER: str = "mock"  # mock|medgemma|gemini|cloud
    MEDGEMMA_ENDPOINT: str = "http://models:8002/v1"

    # --- Cloud (Gemini 3.5 Flash does BOTH extraction + reasoning) ---
    CLOUD_API_PROVIDER: str = "gemini"  # gemini|openai (gemini is default)
    GOOGLE_API_KEY: str = ""  # https://aistudio.google.com/apikey
    OPENAI_API_KEY: str = ""  # fallback only

    # --- Telegram bot ---
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_SECRET: str = ""  # optional webhook verification
    BRIEF_BASE_URL: str = "http://localhost:3000"  # public brief page base
    PUBLIC_URL: str = ""  # ngrok / production URL for webhook registration

    # --- Demo ---
    DEMO_MODE: bool = False
    SEED_PATIENT_ID: str = "pat_demo"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
