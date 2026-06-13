"""Cloud frontier VLM fallback extractor (claude|openai|mistral).

Used when the local Qwen endpoint is unavailable. Selected via CLOUD_VLM_PROVIDER
+ CLOUD_VLM_API_KEY. Implemented for the OpenAI-compatible chat shape (works for
OpenAI and Mistral); the Anthropic path uses the messages API. If unconfigured,
raises so the routing chain falls through to seeded mock.
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.schemas.claims import ClaimsJSON
from app.services.extraction.base import ExtractorProvider
from app.services.extraction.qwen import EXTRACTION_PROMPT, _coerce_claims

logger = logging.getLogger("setu.cloud")

_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "claude": "https://api.anthropic.com/v1/messages",
}
_MODELS = {
    "openai": "gpt-4o",
    "mistral": "pixtral-large-latest",
    "claude": "claude-opus-4-8",
}


def _b64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


class CloudExtractor(ExtractorProvider):
    name = "cloud"

    async def extract(self, file_path: str, mime: str, *, patient_id: str, document_id: str) -> ClaimsJSON:
        provider = settings.CLOUD_VLM_PROVIDER
        if not provider or not settings.CLOUD_VLM_API_KEY:
            raise RuntimeError("cloud VLM not configured")

        b64 = _b64(file_path)
        if provider == "claude":
            raw = await self._call_anthropic(b64, mime)
        else:
            raw = await self._call_openai_compatible(provider, b64, mime)
        return _coerce_claims(raw, document_id, patient_id, f"cloud:{provider}")

    async def _call_openai_compatible(self, provider: str, b64: str, mime: str) -> dict:
        payload = {
            "model": _MODELS[provider],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.CLOUD_VLM_API_KEY}"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(_ENDPOINTS[provider], json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    async def _call_anthropic(self, b64: str, mime: str) -> dict:
        payload = {
            "model": _MODELS["claude"],
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        }
        headers = {
            "x-api-key": settings.CLOUD_VLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(_ENDPOINTS["claude"], json=payload, headers=headers)
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
        return json.loads(text)


# keep timestamp import used (mirrors qwen module structure)
_ = datetime.now(timezone.utc)
