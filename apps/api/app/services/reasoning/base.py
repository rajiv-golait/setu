"""ReasonerProvider interface.

The provider produces PROSE/content (one-liners, chief concern, plain-language
summaries). Safety FLAGS are computed by code in services/brief.py, never by the
model. Providers must return data conforming to the brief/summary content shape;
the brief engine merges deterministic flags afterward.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.memory import CurrentTruthDTO


class ReasonerProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate_brief(self, current_truth: CurrentTruthDTO) -> dict:
        """Return a dict with the prose/content fields of a Doctor Brief.

        Expected keys: one_line, chief_concern, active_medications, recent_labs,
        active_conditions, allergies, timeline, suggested_questions. The brief
        engine adds brief_id, flags, source_documents, confidence_notes.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_summary(
        self, current_truth: CurrentTruthDTO, brief: dict, lang: str
    ) -> dict:
        """Return a dict with patient-summary content fields in `lang`.

        Expected keys: greeting, what_we_found, your_medicines, what_to_watch,
        next_steps, disclaimer.
        """
        raise NotImplementedError
