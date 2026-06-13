"""Reasoner selection by REASONING_PROVIDER env var. Default: mock."""
from __future__ import annotations

from app.config import settings
from app.services.reasoning.base import ReasonerProvider
from app.services.reasoning.medgemma import MedGemmaReasoner
from app.services.reasoning.mock import MockReasoner


def get_reasoner() -> ReasonerProvider:
    if settings.REASONING_PROVIDER == "medgemma":
        return MedGemmaReasoner()
    return MockReasoner()
