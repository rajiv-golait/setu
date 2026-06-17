"""Central configuration. ALL environment variables live here (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parents[1]  # apps/api
_REPO_ROOT = Path(__file__).resolve().parents[3]  # repo root

# Load repo-root .env first, then apps/api/.env (local overrides).
_ENV_FILES = (
    str(_REPO_ROOT / ".env"),
    str(_API_ROOT / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core (Postgres is hosted on Supabase — set DATABASE_URL in .env) ---
    DATABASE_URL: str
    SUPABASE_DB_PASSWORD: str = ""  # substitutes [password] in DATABASE_URL when set
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    SECRET_KEY: str = "dev-only"
    LOG_LEVEL: str = "info"

    # --- Upload / storage ---
    MAX_UPLOAD_MB: int = 15
    STORAGE_PATH: str = "/data/uploads"
    # Retention: keep the raw image through the care window so "verify against
    # original" works, then auto-purge it (structured claims + hash are kept).
    RAW_RETENTION_DAYS: int = 60  # DPDP: 30-90 day window, configurable

    # --- Memory / reducer ---
    CONFIDENCE_THRESHOLD: float = 0.7

    # --- Sharing ---
    SHARE_BASE_URL: str = "http://localhost:3000/share"

    # --- AI providers ---
    # Live path defaults to cloud (Gemini); the routing chain falls back to mock
    # on any failure, so a missing key / API hiccup degrades gracefully. DEMO_MODE
    # is the separate, zero-dependency safety path (untouched by this default).
    EXTRACTION_PROVIDER: str = "cloud"  # mock|qwen|cloud
    QWEN_ENDPOINT: str = "http://models:8001/v1"
    REASONING_PROVIDER: str = "cloud"  # mock|medgemma|gemini|cloud
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

    # --- Supabase auth ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_ENABLED: bool = False

    # --- Demo ---
    DEMO_MODE: bool = False
    SEED_PATIENT_ID: str = "pat_demo"

    @model_validator(mode="before")
    @classmethod
    def _inject_db_password(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        url = data.get("DATABASE_URL")
        pwd = data.get("SUPABASE_DB_PASSWORD") or ""
        if pwd and isinstance(url, str):
            encoded = quote_plus(str(pwd))
            data["DATABASE_URL"] = url.replace("[password]", encoded).replace(
                "[YOUR_DB_PASSWORD]", encoded
            )
        return data

    @property
    def database_url_unresolved(self) -> bool:
        return "[password]" in self.DATABASE_URL or "[YOUR_DB_PASSWORD]" in self.DATABASE_URL

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
