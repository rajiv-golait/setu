"""SETU API entrypoint. Router mount, CORS, lifespan, error envelope handlers."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_exception_handlers
from app.routers import (
    brief,
    documents,
    jobs,
    memory,
    patients,
    referrals,
    shares,
    summary,
    telegram,
    webchat,
)

logging.basicConfig(level=settings.LOG_LEVEL.upper())

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Models are reached over HTTP and never loaded here. Nothing to warm in-process.
    logging.getLogger("setu").info(
        "SETU API starting (extraction=%s, reasoning=%s, demo=%s)",
        settings.EXTRACTION_PROVIDER, settings.REASONING_PROVIDER, settings.DEMO_MODE,
    )
    yield


app = FastAPI(title="SETU API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for r in (patients, documents, jobs, memory, brief, summary, shares, referrals, webchat):
    app.include_router(r.router, prefix=API_PREFIX)

# Telegram webhook is mounted WITHOUT the /api/v1 prefix: register the webhook
# URL as {PUBLIC_URL}/telegram/webhook.
app.include_router(telegram.router, prefix="/telegram")


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "demo_mode": settings.DEMO_MODE}
