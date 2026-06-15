"""Plain-language explanation for the caregiver (Telegram / web-chat reply).

This is the safety boundary around the reasoner's free-text output. The rules
here are NON-NEGOTIABLE and enforced in code, never trusted to the model:

  1. Never suggest starting, stopping, or changing a dose (banned phrases).
  2. Always end with the language-appropriate disclaimer (appended if missing).
  3. overall_confidence < 0.6 -> append a "verify against the original" note.
  4. Never introduce a fact not in the extracted claims (the reasoner is given
     only Current Truth; the prompt forbids new facts).
  5. overall_confidence < 0.4 -> ABSTAIN: do not call the model at all.
"""
from __future__ import annotations

import logging

from app.schemas.memory import CurrentTruthDTO
from app.services.reasoning.base import ReasonerProvider

logger = logging.getLogger("setu.explanation")

ABSTAIN_THRESHOLD = 0.4
LOW_CONFIDENCE_THRESHOLD = 0.6

DISCLAIMER = {
    "mr": "हे तुमच्या कागदाचे स्पष्टीकरण आहे, वैद्यकीय सल्ला नाही.",
    "hi": "यह आपके दस्तावेज़ का स्पष्टीकरण है, चिकित्सीय सलाह नहीं।",
    "en": "This is an explanation of your document, not medical advice.",
}

ABSTAIN_MESSAGE = {
    "mr": "फोटो अस्पष्ट आहे. कृपया स्पष्ट फोटो पाठवा.",
    "hi": "तस्वीर धुंधली है। कृपया एक स्पष्ट तस्वीर भेजें।",
    "en": "The photo is unclear. Please send a clearer photo.",
}

LOW_CONFIDENCE_NOTE = {
    "mr": "काही भाग वाचणे कठीण होते — मूळ कागद तपासा.",
    "hi": "कुछ हिस्से पढ़ना कठिन था — मूल दस्तावेज़ जाँचें।",
    "en": "Some parts were hard to read — please verify against the original.",
}

# Never let any of these reach the caregiver (case-insensitive substring match).
BANNED_PHRASES = (
    "dose badhao",
    "band karo",
    "increase dose",
    "decrease dose",
    "stop taking",
    "change your medication",
    "take instead",
    "switch to",
)


def _disclaimer(lang: str) -> str:
    return DISCLAIMER.get(lang, DISCLAIMER["mr"])


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

    # Rule 1/2 — banned-phrase rejection. We cannot safely "retry" deterministically
    # here, so we drop the unsafe sentence and fall back to a minimal safe message.
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

    # Rule 2 — disclaimer enforcement (append if the model omitted it).
    disclaimer = _disclaimer(lang)
    if disclaimer not in text:
        text = text.rstrip() + " " + disclaimer

    return text.strip()
