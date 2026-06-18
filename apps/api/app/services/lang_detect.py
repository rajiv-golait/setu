"""Lightweight chat language detection — profile lang is the fallback."""
from __future__ import annotations

import re

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_LATIN = re.compile(r"[A-Za-z]")

# Letters uncommon in Hindi but used in Marathi.
_MR_CHARS = re.compile(r"[ळऱॅऑ]")

_MR_WORDS = re.compile(
    r"(मी|तुम्ही|आहे|नाही|काय|माझ|तुझ|तुमच|म्हण|होत|येत|झाल|औषध|नमस्कार)",
)
_HI_WORDS = re.compile(
    r"(मैं|मेरा|मेरी|आप|हैं|है|नहीं|क्या|क्यों|कैसे|भाई|दर्द|बताओ|दवा|नमस्ते)",
)

_HI_ROMAN = re.compile(
    r"\b("
    r"bhaiya?|mera|meri|mere|mujhe|mujhse|kya|kyun|kaise|kaisa|"
    r"hai|hain|nahi|nahin|nai|aap|apko|dard|batao|bata|karo|"
    r"dawai|bimar|bukhar|pet|sir|matha|jab|tab|abhi|"
    r"raha|rahi|rahe|gaya|gayi|ja|jaa|kuch|yeh|ye|woh|wo"
    r")\b",
    re.IGNORECASE,
)
_EN_WORDS = re.compile(
    r"\b("
    r"the|is|are|was|what|how|why|my|your|pain|doctor|medicine|help|"
    r"please|can|have|feel|headache|chest|fever|patch|skin|not|going"
    r")\b",
    re.IGNORECASE,
)


def resolve_reply_lang(
    message: str,
    profile_lang: str = "mr",
    history: list[dict] | None = None,
) -> str:
    """Pick mr / hi / en for Saathi replies from the user's words."""
    profile = profile_lang if profile_lang in ("mr", "hi", "en") else "mr"

    snippets = [message]
    if history:
        for turn in history[-4:]:
            if turn.get("role") == "user":
                snippets.append(str(turn.get("content", "")))

    combined = " ".join(snippets).strip()
    if not combined:
        return profile

    if _DEVANAGARI.search(combined):
        mr_score = len(_MR_CHARS.findall(combined)) * 3 + len(_MR_WORDS.findall(combined)) * 2
        hi_score = len(_HI_WORDS.findall(combined)) * 2
        if mr_score > hi_score:
            return "mr"
        if hi_score > mr_score:
            return "hi"
        return profile if profile in ("mr", "hi") else "mr"

    if not _LATIN.search(combined):
        return profile

    hi_score = len(_HI_ROMAN.findall(combined))
    en_score = len(_EN_WORDS.findall(combined))

    if hi_score >= 2 and hi_score >= en_score:
        return "hi"
    if hi_score >= 1 and en_score == 0:
        return "hi"
    if en_score >= 1 and en_score > hi_score:
        return "en"
    if hi_score >= 1 and hi_score >= en_score:
        return "hi"

    return profile
