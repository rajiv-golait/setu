"""ExtractorProvider interface. image/PDF -> Claims JSON."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.claims import ClaimsJSON


class ExtractorProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def extract(self, file_path: str, mime: str, *, patient_id: str, document_id: str) -> ClaimsJSON:
        """Read a document and return structured Claims JSON.

        Implementations must NOT raise on low confidence — they should set
        per-claim confidence / needs_review and let validation gate downstream.
        Hard failures (unreadable, provider down) may raise; the orchestrator's
        routing chain handles fallback.
        """
        raise NotImplementedError
