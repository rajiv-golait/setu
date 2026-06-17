"""Test fixtures: in-memory SQLite (async) + fake Redis, so the full app runs
with zero external services. Mock providers keep it GPU-free.
"""
from __future__ import annotations

import os

# Satisfy required DATABASE_URL before app.config loads (tests use SQLite via monkeypatch).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:1/unused")

import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import models  # noqa: F401 — register tables
from app.db.base import Base


# --- Fake in-memory Redis for job state ----------------------------------- #
class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(self, key, value, ex=None):  # noqa: ANN001
        self._store[key] = value

    async def get(self, key):  # noqa: ANN001
        return self._store.get(key)


@pytest.fixture(autouse=True)
def _use_mock_ai_for_tests(monkeypatch):
    """Tests use mock AI directly — live path must not silently fall back to seed data."""
    from app import config

    monkeypatch.setattr(config.settings, "EXTRACTION_PROVIDER", "mock")
    monkeypatch.setattr(config.settings, "REASONING_PROVIDER", "mock")


@pytest.fixture(autouse=True)
def _disable_supabase_auth(monkeypatch):
    """Tests run in legacy anonymous mode unless a test opts into auth."""
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", False)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", "")


@pytest.fixture(autouse=True)
def _writable_storage_path(tmp_path, monkeypatch):
    """CI and local dev may default STORAGE_PATH to /data/uploads (not writable)."""
    from app import config

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(config.settings, "STORAGE_PATH", str(upload_dir))


@pytest.fixture(autouse=True)
def _patch_redis(monkeypatch):
    fake = FakeRedis()
    from app import jobs_store

    monkeypatch.setattr(jobs_store, "_redis", lambda: fake)
    return fake


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine, monkeypatch):
    """SQLite-backed factory. Also repoints every module that captured the real
    SessionLocal by value (orchestrator) so the pipeline never touches Postgres.
    """
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)

    from app.db import session as session_module
    from app.services import orchestrator

    monkeypatch.setattr(session_module, "engine", db_engine)
    monkeypatch.setattr(session_module, "SessionLocal", factory)
    monkeypatch.setattr(orchestrator, "SessionLocal", factory)
    return factory


@pytest_asyncio.fixture
async def client(session_factory):
    """App client wired to the in-memory DB."""
    from app.db import session as session_module
    from app.main import app

    async def _get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[session_module.get_db] = _get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


def loads(resp) -> dict:
    return json.loads(resp.content)
