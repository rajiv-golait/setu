"""Saathi chatbot tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.saathi import chat


def _truth_with_meds() -> CurrentTruthDTO:
    return CurrentTruthDTO(
        patient_id="pat_s1",
        generated_at=datetime.now(timezone.utc),
        entries=[
            CurrentTruthEntry(
                entry_type="medication",
                normalized_key="metformin",
                state="confirmed",
                value={"name": "Metformin", "dose": 500, "dose_unit": "mg", "frequency": "twice daily"},
                confidence=0.9,
                source_claim_ids=["c1"],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_identity_question_no_gemini():
    res = await chat("pat_s1", "who are u", [], _truth_with_meds(), "en")
    assert res.action == "none"
    assert "Saathi" in res.reply
    assert "doctor" not in res.reply.lower() or "that's for your doctor" in res.reply.lower()


@pytest.mark.asyncio
async def test_empty_records_prompts_upload():
    empty = CurrentTruthDTO(
        patient_id="pat_s1",
        entries=[],
        generated_at=datetime.now(timezone.utc),
    )
    res = await chat("pat_s1", "what medicines am I on?", [], empty, "en")
    assert res.action == "none"
    assert "upload" in res.reply.lower()


@pytest.mark.asyncio
async def test_gemini_failure_returns_neutral_error(monkeypatch):
    async def _boom(*_a, **_k):
        raise RuntimeError("quota")

    monkeypatch.setattr("app.services.gemini_client.generate_content_with_fallback", _boom)
    res = await chat("pat_s1", "what is metformin for?", [], _truth_with_meds(), "en")
    assert res.action == "none"
    assert "try again" in res.reply.lower()
    assert "document" not in res.reply.lower()


def test_resolve_hinglish_as_hindi():
    from app.services.lang_detect import resolve_reply_lang

    assert (
        resolve_reply_lang("bhai mera woh forehead ka patch ja hi nai raha", "mr")
        == "hi"
    )


def test_resolve_english_as_english():
    from app.services.lang_detect import resolve_reply_lang

    assert resolve_reply_lang("what medicines am I taking?", "mr") == "en"


def test_resolve_marathi_devanagari():
    from app.services.lang_detect import resolve_reply_lang

    assert resolve_reply_lang("माझी औषधे काय आहेत?", "en") == "mr"


def test_resolve_hindi_devanagari():
    from app.services.lang_detect import resolve_reply_lang

    assert resolve_reply_lang("मेरी दवाइयाँ क्या हैं?", "mr") == "hi"


def test_ambiguous_short_message_uses_profile():
    from app.services.lang_detect import resolve_reply_lang

    assert resolve_reply_lang("ok", "mr") == "mr"
    assert resolve_reply_lang("ok", "en") == "en"
