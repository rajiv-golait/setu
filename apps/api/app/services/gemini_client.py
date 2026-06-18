"""Shared Gemini generateContent helper with free-tier model fallbacks."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Any

from app.services.gemini_models import GEMINI_FREE_TIER_MODELS

logger = logging.getLogger("setu.gemini")

_RETRY_BACKOFF_SECONDS = (1.5, 3.0, 6.0)


def is_transient_gemini_error(exc: Exception) -> bool:
    """503 / overload — worth retrying on the same model."""
    msg = str(exc).upper()
    return any(token in msg for token in ("503", "UNAVAILABLE", "OVERLOADED", "HIGH DEMAND"))


def is_quota_exhausted(exc: Exception) -> bool:
    """Free-tier / billing quota — retrying the same model won't help."""
    msg = str(exc).upper()
    return "RESOURCE_EXHAUSTED" in msg or "LIMIT: 0" in msg or "QUOTA EXCEEDED" in msg


def is_model_not_found(exc: Exception) -> bool:
    msg = str(exc).upper()
    return "404" in msg or "NOT_FOUND" in msg or "IS NOT FOUND" in msg


async def generate_content_with_fallback(
    client: Any,
    *,
    contents: Any,
    config: Any,
    models: Sequence[str] = GEMINI_FREE_TIER_MODELS,
) -> tuple[Any, str]:
    """Try each model in order; return (response, model_id_used)."""
    last_exc: Exception | None = None
    quota_hit = False

    for model in models:
        max_attempts = 1 if quota_hit else len(_RETRY_BACKOFF_SECONDS)
        for attempt, delay in enumerate(_RETRY_BACKOFF_SECONDS[:max_attempts]):
            if attempt > 0:
                await asyncio.sleep(delay)
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                if model != models[0]:
                    logger.warning("gemini fell back to %s", model)
                return response, model
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if is_model_not_found(e):
                    logger.warning("gemini %s not available, skipping", model)
                    break
                if is_quota_exhausted(e):
                    quota_hit = True
                    logger.warning("gemini %s quota exhausted: %s", model, e)
                    break
                if is_transient_gemini_error(e):
                    if attempt == 0:
                        logger.warning(
                            "gemini %s transient error (attempt 1): %s", model, e
                        )
                        await asyncio.sleep(0.5)
                        continue
                    logger.warning("gemini %s still unavailable, trying next model", model)
                    break
                logger.warning("gemini %s failed: %s", model, e)
                break

    raise RuntimeError(f"all Gemini models failed: {last_exc}") from last_exc


async def validate_model_chain() -> None:
    """Probe each model in the chain at startup and log availability.

    Errors are logged only — never raised. A model that fails the probe will
    naturally be skipped (NOT_FOUND/quota) during real calls.
    """
    from app.config import settings

    if not settings.GOOGLE_API_KEY:
        logger.info("gemini validation skipped (no GOOGLE_API_KEY)")
        return

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning("gemini validation skipped (SDK import failed): %s", exc)
        return

    for model in GEMINI_FREE_TIER_MODELS:
        try:
            await client.aio.models.generate_content(
                model=model,
                contents="hi",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    max_output_tokens=1,
                ),
            )
            logger.info("gemini chain: %s ✓", model)
        except Exception as exc:  # noqa: BLE001
            logger.warning("gemini chain: %s ✗ (%s)", model, exc)
