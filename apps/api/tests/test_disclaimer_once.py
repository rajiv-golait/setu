"""D-C1: disclaimer must appear exactly once in the final explanation text."""
from __future__ import annotations

import pytest

from app.schemas.memory import CurrentTruthDTO
from app.services.explanation import generate_explanation
from app.services.reasoning.mock import MockReasoner
from app.services.safety import DISCLAIMER

pytestmark = pytest.mark.asyncio

_EMPTY_TRUTH = CurrentTruthDTO(
    patient_id="pat_test",
    entries=[],
    generated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
)


@pytest.mark.parametrize("lang", ["mr", "hi", "en"])
async def test_disclaimer_appears_exactly_once(lang: str) -> None:
    text = await generate_explanation(
        _EMPTY_TRUTH, lang, "prescription", MockReasoner(), overall_confidence=0.9
    )
    disc = DISCLAIMER[lang]
    count = text.count(disc)
    assert count == 1, (
        f"Disclaimer appeared {count} times in {lang!r} explanation.\n\n"
        f"Full text:\n{text}"
    )
