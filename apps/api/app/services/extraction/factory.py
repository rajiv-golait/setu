"""Extractor selection + production routing chain.

EXTRACTION_PROVIDER selects the provider:
  cloud -> CloudExtractor (Gemini + OpenAI fallback). Failures surface as job errors.
  qwen  -> QwenExtractor -> CloudExtractor fallback. Failures surface as job errors.
  mock  -> MockExtractor only (dev/test fixtures — never served to real users).

There are no silent fake-data fallbacks. If the real provider fails, the job
fails with a clear error and a retry button is shown to the user.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.schemas.claims import ClaimsJSON
from app.services.extraction.base import ExtractorProvider
from app.services.extraction.cloud import CloudExtractor
from app.services.extraction.qwen import QwenExtractor

logger = logging.getLogger("setu.extraction")


def _chain() -> list[ExtractorProvider]:
    provider = settings.EXTRACTION_PROVIDER
    if provider == "qwen":
        return [QwenExtractor(), CloudExtractor()]
    if provider == "cloud":
        return [CloudExtractor()]
    # "mock" — explicit dev/test mode; never reached in production.
    from app.services.extraction.mock import MockExtractor
    return [MockExtractor()]


async def extract_with_fallback(
    file_path: str, mime: str, *, patient_id: str, document_id: str
) -> ClaimsJSON:
    chain = _chain()
    last_exc: Exception | None = None
    for provider in chain:
        try:
            result = await provider.extract(file_path, mime, patient_id=patient_id, document_id=document_id)
            if provider is not chain[0]:
                logger.warning("extraction fell back to %s", provider.name)
            return result
        except Exception as exc:  # noqa: BLE001 — try next provider in chain
            last_exc = exc
            logger.warning("extractor %s failed: %s", provider.name, exc)
    raise RuntimeError(f"all extractors failed: {last_exc}")
