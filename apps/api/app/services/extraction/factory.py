"""Extractor selection + production routing chain.

EXTRACTION_PROVIDER selects the *primary*:
  mock  -> MockExtractor only (default; CI/dev, zero GPU)
  qwen  -> try Qwen, then Cloud, then seeded Mock (never fail silently)
  cloud -> try Cloud, then seeded Mock

extract_with_fallback() implements the chain and always returns Claims JSON.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.schemas.claims import ClaimsJSON
from app.services.extraction.base import ExtractorProvider
from app.services.extraction.cloud import CloudExtractor
from app.services.extraction.mock import MockExtractor
from app.services.extraction.qwen import QwenExtractor

logger = logging.getLogger("setu.extraction")


def _chain() -> list[ExtractorProvider]:
    provider = settings.EXTRACTION_PROVIDER
    if provider == "qwen":
        return [QwenExtractor(), CloudExtractor(), MockExtractor()]
    if provider == "cloud":
        return [CloudExtractor(), MockExtractor()]
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
    # Chain is guaranteed to end in MockExtractor, which never raises — but be safe.
    raise RuntimeError(f"all extractors failed: {last_exc}")
