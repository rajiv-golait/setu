"""B5 — Hindi end-to-end through the deterministic mock path (which is also the
cloud fallback). Explanation + summary must render in Hindi, never silently
falling back to Marathi or English.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services import explanation as ex
from app.services.reasoning.mock import MockReasoner
from app.services.safety import DISCLAIMER
from app.services.summary import build_summary

pytestmark = pytest.mark.asyncio


def _truth() -> CurrentTruthDTO:
    return CurrentTruthDTO(
        patient_id="p", generated_at=datetime.now(timezone.utc),
        entries=[
            CurrentTruthEntry(
                entry_type="lab_result", normalized_key="hba1c",
                value={"test_name": "HbA1c", "value": 9.1, "unit": "%", "trend": "up", "previous": 8.4, "flag": "high"},
                confidence=0.95,
            ),
        ],
    )


async def test_explanation_renders_in_hindi():
    text = await ex.generate_explanation(_truth(), "hi", "lab_result", MockReasoner(), overall_confidence=0.9)
    assert DISCLAIMER["hi"] in text
    assert "तुमची" not in text  # not Marathi
    assert "Please speak with your doctor" not in text  # not English


async def test_summary_renders_in_hindi():
    brief = DoctorBriefDTO(
        brief_id="b", patient_id="p", generated_at=datetime.now(timezone.utc), model="mock",
        one_line="x", chief_concern="y",
        recent_labs=[{"test": "HbA1c", "value": 9.1, "unit": "%", "flag": "high", "trend": "up", "previous": 8.4}],
        active_medications=[{"name": "Metformin", "dose": "500mg", "frequency": "BD"}],
    )
    summary = await build_summary("p", _truth(), brief, MockReasoner(), lang="hi")
    assert summary.language == "hi"
    # Hindi greeting + disclaimer, not the Marathi/English ones.
    assert "नमस्ते" in summary.greeting
    assert "चिकित्सीय सलाह" in summary.disclaimer
