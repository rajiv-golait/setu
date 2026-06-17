"""Safety constants and helpers shared across the explanation and reasoning layers.

These are the non-negotiable rules enforced in code, never trusted to any model:
  1. Disclaimer is always appended by code — the model is instructed not to include it.
  2. Banned phrases are stripped before any text reaches the user.
  3. Abstain on unreadable documents (confidence < 0.4) — never invent.
  4. Low-confidence note when extraction confidence < 0.6.
"""
from __future__ import annotations

DISCLAIMER: dict[str, str] = {
    "mr": "हे तुमच्या कागदाचे स्पष्टीकरण आहे, वैद्यकीय सल्ला नाही. डॉक्टरांशी बोला.",
    "hi": "यह आपके दस्तावेज़ का स्पष्टीकरण है, चिकित्सीय सलाह नहीं। डॉक्टर से बात करें।",
    "en": "This is an explanation of your document, not medical advice. Please speak with your doctor.",
}

ABSTAIN_MESSAGE: dict[str, str] = {
    "mr": "फोटो अस्पष्ट आहे. कृपया स्पष्ट फोटो पाठवा.",
    "hi": "तस्वीर धुंधली है। कृपया एक स्पष्ट तस्वीर भेजें।",
    "en": "The photo is unclear. Please send a clearer photo.",
}

LOW_CONFIDENCE_NOTE: dict[str, str] = {
    "mr": "काही भाग वाचणे कठीण होते — मूळ कागद तपासा.",
    "hi": "कुछ हिस्से पढ़ना कठिन था — मूल दस्तावेज़ जाँचें।",
    "en": "Some parts were hard to read — please verify against the original.",
}

# Never let any of these reach the caregiver (case-insensitive substring match).
BANNED_PHRASES: tuple[str, ...] = (
    "dose badhao",
    "band karo",
    "increase dose",
    "decrease dose",
    "stop taking",
    "change your medication",
    "take instead",
    "switch to",
)

ABSTAIN_THRESHOLD: float = 0.4
LOW_CONFIDENCE_THRESHOLD: float = 0.6


def append_disclaimer(text: str, lang: str) -> str:
    """Always append the canonical disclaimer — deterministic, no substring check."""
    disc = DISCLAIMER.get(lang, DISCLAIMER["en"])
    return text.rstrip() + "\n\n" + disc
