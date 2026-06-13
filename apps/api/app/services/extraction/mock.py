"""Mock extractor — DEFAULT. Returns the seeded demo Claims JSON regardless of
input file. Zero GPU. Keeps the pipeline green and is the final fallback in the
production routing chain.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from app.schemas.claims import Claim, ClaimsJSON
from app.seed.fixtures import demo_claims
from app.services.extraction.base import ExtractorProvider


class MockExtractor(ExtractorProvider):
    name = "mock"

    async def extract(self, file_path: str, mime: str, *, patient_id: str, document_id: str) -> ClaimsJSON:
        raw = demo_claims(patient_id)
        claims = [
            Claim(
                claim_id=c["claim_id"],
                type=c["type"],
                fields=c["fields"],
                confidence=c["confidence"],
                observed_at=date.fromisoformat(c["observed_at"]) if c.get("observed_at") else None,
                needs_review=c.get("needs_review", False),
            )
            for c in raw
        ]
        overall = round(sum(float(c.confidence) for c in claims) / len(claims), 2) if claims else 0.0
        return ClaimsJSON(
            document_id=document_id,
            patient_id=patient_id,
            extracted_at=datetime.now(timezone.utc),
            provider=self.name,
            document_type="prescription",
            overall_confidence=overall,
            claims=claims,
        )
