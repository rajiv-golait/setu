"""Reasoner selection by REASONING_PROVIDER env var. Default: mock."""
from __future__ import annotations

from app.config import settings
from app.services.reasoning.base import ReasonerProvider
from app.services.reasoning.cloud import GeminiReasonerProvider
from app.services.reasoning.medgemma import MedGemmaReasoner
from app.services.reasoning.mock import MockReasoner


def get_reasoner() -> ReasonerProvider:
    provider = settings.REASONING_PROVIDER
    if provider == "medgemma":
        return MedGemmaReasoner()
    if provider in ("gemini", "cloud"):
        return GeminiReasonerProvider()
    return MockReasoner()
