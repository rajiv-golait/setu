"""Gemini model IDs for generateContent.

Docs: https://ai.google.dev/gemini-api/docs/models

Two-model chain per plan.md appendix (June 2026):
  - gemini-3.5-flash: GA primary — best structured document extraction on free tier
  - gemini-3.1-flash-lite: GA fallback — cheapest GA model, highest free RPD

Dead IDs removed to avoid burning 10s+ walking 404s during fallback.
"""

from __future__ import annotations

GEMINI_MODEL_CHAIN: tuple[str, ...] = (
    "gemini-3.5-flash",      # GA primary — best for structured OCR extraction
    "gemini-3.1-flash-lite", # GA fallback — cheapest, highest free RPD
)

# Back-compat alias used by gemini_client default.
GEMINI_FREE_TIER_MODELS = GEMINI_MODEL_CHAIN

GEMINI_DEFAULT_MODEL = GEMINI_MODEL_CHAIN[0]
