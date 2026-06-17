"""Plain-language explanation for the caregiver (Telegram / web-chat reply).

Safety rules enforced in code, never trusted to the model:
  1. Never suggest starting, stopping, or changing a dose (banned phrases).
  2. Always end with the language-appropriate disclaimer (always appended by code).
  3. overall_confidence < 0.6 -> append a "verify against the original" note.
  4. Never introduce a fact not in the extracted claims.
  5. overall_confidence < 0.4 -> ABSTAIN: do not call the model at all.
"""
from __future__ import annotations

import logging

from app.schemas.memory import CurrentTruthDTO
from app.services.reasoning.base import ReasonerProvider
from app.services.safety import (
    ABSTAIN_MESSAGE,
    ABSTAIN_THRESHOLD,
    BANNED_PHRASES,
    LOW_CONFIDENCE_NOTE,
    LOW_CONFIDENCE_THRESHOLD,
    append_disclaimer,
)

logger = logging.getLogger("setu.explanation")


def _contains_banned(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in BANNED_PHRASES)


async def generate_explanation(
    current_truth: CurrentTruthDTO,
    lang: str,
    doc_type: str,
    reasoner: ReasonerProvider,
    overall_confidence: float = 1.0,
) -> str:
    """Generate a safe, plain-language explanation string in `lang`.

    `overall_confidence` is the extraction confidence; it drives the abstain
    (<0.4) and low-confidence-note (<0.6) gates.
    """
    # Rule 5 — abstain on unreadable documents (never call the model).
    if overall_confidence < ABSTAIN_THRESHOLD:
        logger.info("explanation abstained: overall_confidence=%.2f", overall_confidence)
        return ABSTAIN_MESSAGE.get(lang, ABSTAIN_MESSAGE["mr"])

    text = await reasoner.generate_explanation(current_truth, lang, doc_type)
    text = (text or "").strip()

    # Rule 1 — banned-phrase rejection: drop the unsafe text and use a safe fallback.
    if _contains_banned(text):
        logger.warning("explanation contained a banned phrase; replacing with safe minimal text")
        safe = {
            "mr": "तुमच्या कागदाची माहिती वाचली आहे. कृपया डॉक्टरांशी बोला.",
            "hi": "आपके दस्तावेज़ की जानकारी पढ़ी गई है। कृपया डॉक्टर से बात करें।",
            "en": "Your document has been read. Please speak with your doctor.",
        }
        text = safe.get(lang, safe["mr"])

    # Rule 3 — low-confidence verify note (before the disclaimer).
    if overall_confidence < LOW_CONFIDENCE_THRESHOLD:
        note = LOW_CONFIDENCE_NOTE.get(lang, LOW_CONFIDENCE_NOTE["mr"])
        if note not in text:
            text = text.rstrip(".") + ". " + note

    # Rule 2 — disclaimer always appended by code (model is instructed not to include it).
    return append_disclaimer(text, lang)
