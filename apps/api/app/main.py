"""SETU API entrypoint. Router mount, CORS, lifespan, error envelope handlers."""
from __future__ import annotations

import asyncio
import logging
import sys

# psycopg async requires SelectorEventLoop on Windows (ProactorEventLoop breaks).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text

from app.config import settings
from app.errors import register_exception_handlers
from app.routers import admin_appointments_router as admin_appointments
from app.routers import admin_patients_router as admin_patients
from app.routers import admin_providers_router as admin_providers
from app.routers import analytics_router as analytics
from app.routers import appointments_router as appointments
from app.routers import auth_router as auth
from app.routers import availability_router as availability
from app.routers import (
    brief,
    chat,
    consent,
    documents,
    jobs,
    memory,
    patients,
    providers,
    push,
    referrals,
    reminders,
    shares,
    summary,
    telegram,
    webchat,
)
from app.routers import encounters_router as encounters
from app.routers import fhir_gateway_router as fhir_gateway
from app.routers import health_worker_router as workers
from app.routers import notifications_router as notifications
from app.routers import support_router as support
from app.routers import symptom_chat_router as symptom_chat
from app.routers import timeline_router as timeline
from app.routers import triage_router as triage
from app.routers import vitals_router as vitals

logging.basicConfig(level=settings.LOG_LEVEL.upper())

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Models are reached over HTTP and never loaded here. Nothing to warm in-process.
    logging.getLogger("setu").info(
        "SETU API starting (extraction=%s, reasoning=%s, production=%s)",
        settings.EXTRACTION_PROVIDER,
        settings.REASONING_PROVIDER,
        settings.PRODUCTION,
    )
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("setu").warning("sentry init skipped: %s", exc)
    if settings.database_url_unresolved:
        logging.getLogger("setu").error(
            "DATABASE_URL still contains [password] — set SUPABASE_DB_PASSWORD in .env"
        )
    # Validate Gemini model chain at startup (async, non-blocking).
    if settings.GOOGLE_API_KEY:
        from app.services.gemini_client import validate_model_chain
        asyncio.create_task(validate_model_chain())
    # Push reminder loop (no-op if VAPID keys not set).
    from app.services.scheduler import reminder_push_loop
    asyncio.create_task(reminder_push_loop())
    # Ensure push_subscriptions table exists (idempotent — migration may not have run yet).
    try:
        from sqlalchemy import text as _text

        from app.db.session import SessionLocal
        async with SessionLocal() as _db:
            await _db.execute(_text(
                "CREATE TABLE IF NOT EXISTS push_subscriptions ("
                "  id TEXT PRIMARY KEY, user_id TEXT NOT NULL, "
                "  endpoint TEXT NOT NULL UNIQUE, p256dh TEXT NOT NULL, "
                "  auth TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now())"
            ))
            await _db.execute(_text(
                "CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id "
                "ON push_subscriptions (user_id)"
            ))
            await _db.commit()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("setu").warning("push_subscriptions table check skipped: %s", exc)
    # Retention sweep on boot: purge raw images past the retention window. Cheap,
    # idempotent, and never blocks startup. (A redeploy/restart is the schedule;
    # a real worker can call retention.purge_expired_documents on a timer.)
    try:
        from app.db.session import SessionLocal
        from app.services.retention import purge_expired_documents

        async with SessionLocal() as db:
            await purge_expired_documents(db)
    except Exception as exc:  # noqa: BLE001 — must never block startup
        logging.getLogger("setu").warning("startup purge skipped: %s", exc)
    yield


app = FastAPI(title="SETU API", version="0.1.0", lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Supabase access token (required when SUPABASE_ENABLED=true)",
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for r in (
    auth,
    patients,
    documents,
    jobs,
    memory,
    brief,
    summary,
    shares,
    referrals,
    webchat,
    chat,
    push,
    consent,
    reminders,
    triage,
    providers,
    availability,
    appointments,
    encounters,
    timeline,
    notifications,
    support,
    symptom_chat,
    fhir_gateway,
    workers,
    vitals,
    analytics,
    admin_providers,
    admin_patients,
    admin_appointments,
):
    app.include_router(r.router, prefix=API_PREFIX)

# Telegram webhook is mounted WITHOUT the /api/v1 prefix: register the webhook
# URL as {PUBLIC_URL}/telegram/webhook.
app.include_router(telegram.router, prefix="/telegram")


@app.get("/health", tags=["health"])
async def health() -> dict:
    out: dict = {"status": "ok"}
    if settings.database_url_unresolved:
        out["status"] = "degraded"
        out["database"] = "misconfigured"
        out["hint"] = "Set SUPABASE_DB_PASSWORD in apps/api/.env"
        return out
    try:
        from app.db.session import SessionLocal

        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        out["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        out["status"] = "degraded"
        out["database"] = type(exc).__name__
        if settings.SECRET_KEY == "dev-only":
            out["hint"] = "Check DATABASE_URL / Supabase pooler host and password"
    return out
