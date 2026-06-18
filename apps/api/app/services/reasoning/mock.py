"""Mock reasoner — DEFAULT. Builds brief/summary content deterministically from
Current Truth. Zero GPU, zero network. This is what keeps the demo core green.

It produces the *prose/content* only; safety flags are layered on by
services/brief.py.
"""
from __future__ import annotations

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.reasoning.base import ReasonerProvider

_TREND_WORD = {"up": "rising", "down": "falling", "stable": "stable"}


def _title(key: str) -> str:
    return key.replace("_", " ").title()


def _meds(entries: list[CurrentTruthEntry]) -> list[CurrentTruthEntry]:
    return [e for e in entries if e.entry_type == "medication"]


def _labs(entries: list[CurrentTruthEntry]) -> list[CurrentTruthEntry]:
    return [e for e in entries if e.entry_type == "lab_result"]


def _conditions(entries: list[CurrentTruthEntry]) -> list[CurrentTruthEntry]:
    return [e for e in entries if e.entry_type == "diagnosis"]


def _allergies(entries: list[CurrentTruthEntry]) -> list[CurrentTruthEntry]:
    return [e for e in entries if e.entry_type == "allergy"]


class MockReasoner(ReasonerProvider):
    name = "mock"

    async def generate_brief(self, current_truth: CurrentTruthDTO) -> dict:
        entries = current_truth.entries
        meds, labs, conds, allergies = _meds(entries), _labs(entries), _conditions(entries), _allergies(entries)

        # one_line: conditions + a notable lab trend.
        cond_str = ", ".join(_title(c.normalized_key) for c in conds) or "no recorded conditions"
        lab_note = ""
        for lab in labs:
            trend = lab.value.get("trend")
            if trend in ("up", "down"):
                lab_note = f" · {lab.value.get('test_name', _title(lab.normalized_key))} {_TREND_WORD[trend]}"
                break
        one_line = f"{cond_str}{lab_note} · here for review".strip()

        chief = "Routine review"
        for lab in labs:
            if lab.value.get("flag") in ("high", "low") or lab.value.get("trend") in ("up", "down"):
                chief = f"Review of {lab.value.get('test_name', _title(lab.normalized_key))}"
                break

        active_medications = []
        for m in meds:
            if m.state == "possibly_discontinued":
                continue
            f = m.value if not m.value.get("conflict") else m.value["values"][0]
            dose = f.get("dose")
            dose_unit = f.get("dose_unit", "")
            active_medications.append(
                {
                    "name": f.get("name", _title(m.normalized_key)),
                    "dose": f"{dose}{dose_unit}" if dose is not None else None,
                    "frequency": f.get("frequency"),
                    "since": (f.get("duration") and None) or f.get("observed_at"),
                    "source": m.source_claim_ids[0] if m.source_claim_ids else None,
                }
            )

        recent_labs = []
        for lab in labs:
            f = lab.value
            recent_labs.append(
                {
                    "test": f.get("test_name", _title(lab.normalized_key)),
                    "value": f.get("value"),
                    "unit": f.get("unit"),
                    "flag": f.get("flag"),
                    "date": (f.get("history") or [{}])[-1].get("date"),
                    "trend": f.get("trend"),
                    "previous": f.get("previous"),
                }
            )

        active_conditions = [
            {
                "condition": (c.value.get("condition") if not c.value.get("conflict") else c.value["values"][0].get("condition"))
                or _title(c.normalized_key),
                "since": c.value.get("observed_at"),
                "source": c.source_claim_ids[0] if c.source_claim_ids else None,
            }
            for c in _conditions(entries)
            if (c.value.get("status") or (c.value.get("values", [{}])[0].get("status")) or "active") != "resolved"
        ]

        allergy_items = [
            {
                "substance": a.value.get("substance", _title(a.normalized_key)),
                "severity": a.value.get("severity"),
            }
            for a in allergies
        ]

        timeline = []
        for lab in labs:
            for h in lab.value.get("history", []):
                if h.get("date"):
                    timeline.append(
                        {"date": h["date"], "event": f"{lab.value.get('test_name', _title(lab.normalized_key))} {h.get('value')}{lab.value.get('unit', '')}"}
                    )
        timeline.sort(key=lambda t: t["date"])

        questions = []
        if meds:
            first = meds[0].value if not meds[0].value.get("conflict") else meds[0].value["values"][0]
            questions.append(f"Adherence to {first.get('name', _title(meds[0].normalized_key))}?")
        questions.append("Any new symptoms or side effects?")
        if labs:
            questions.append("Diet / lifestyle changes since last visit?")

        return {
            "one_line": one_line,
            "chief_concern": chief,
            "active_medications": active_medications,
            "recent_labs": recent_labs,
            "active_conditions": active_conditions,
            "allergies": allergy_items,
            "timeline": timeline,
            "suggested_questions": questions,
        }

    async def generate_explanation(
        self, current_truth: CurrentTruthDTO, lang: str, doc_type: str
    ) -> str:
        """Deterministic plain-language explanation built from Current Truth.

        No model, no network. The disclaimer is appended by
        services/explanation.py, but we include one here too so the raw provider
        output is already safe.
        """
        entries = current_truth.entries
        labs, meds = _labs(entries), _meds(entries)
        if lang == "mr":
            return self._explain_mr(labs, meds)
        if lang == "hi":
            return self._explain_hi(labs, meds)
        return self._explain_en(labs, meds)

    def _explain_mr(self, labs, meds) -> str:  # noqa: ANN001
        parts: list[str] = []
        for lab in labs:
            v = lab.value
            name = v.get("test_name", _title(lab.normalized_key))
            if v.get("trend") == "up" and v.get("previous") is not None:
                parts.append(f"तुमची {name} पातळी ({v.get('value')}) वाढली आहे — मागच्या वेळेपेक्षा ({v.get('previous')}).")
            elif v.get("trend") == "down" and v.get("previous") is not None:
                parts.append(f"तुमची {name} पातळी ({v.get('value')}) कमी झाली आहे.")
        if not parts:
            parts.append("तुमच्या रिपोर्टमध्ये कोणतीही मोठी समस्या आढळली नाही.")
        med_names = [
            (m.value if not m.value.get("conflict") else m.value["values"][0]).get("name", _title(m.normalized_key))
            for m in meds
            if m.state != "possibly_discontinued"
        ]
        if med_names:
            parts.append(f"{' आणि '.join(med_names[:2])} सुरू आहेत.")
        parts.append("कृपया डॉक्टरांशी बोला.")
        return " ".join(parts)

    def _explain_hi(self, labs, meds) -> str:  # noqa: ANN001
        parts: list[str] = []
        for lab in labs:
            v = lab.value
            name = v.get("test_name", _title(lab.normalized_key))
            if v.get("trend") == "up" and v.get("previous") is not None:
                parts.append(f"आपका {name} स्तर ({v.get('value')}) बढ़ा है — पिछली बार ({v.get('previous')}) से।")
            elif v.get("trend") == "down" and v.get("previous") is not None:
                parts.append(f"आपका {name} स्तर ({v.get('value')}) कम हुआ है।")
        if not parts:
            parts.append("आपकी रिपोर्ट में कोई बड़ी समस्या नहीं मिली।")
        med_names = [
            (m.value if not m.value.get("conflict") else m.value["values"][0]).get("name", _title(m.normalized_key))
            for m in meds
            if m.state != "possibly_discontinued"
        ]
        if med_names:
            parts.append(f"{' और '.join(med_names[:2])} चल रही हैं।")
        parts.append("कृपया डॉक्टर से बात करें।")
        return " ".join(parts)

    def _explain_en(self, labs, meds) -> str:  # noqa: ANN001
        parts: list[str] = []
        for lab in labs:
            v = lab.value
            name = v.get("test_name", _title(lab.normalized_key))
            if v.get("trend") in ("up", "down") and v.get("previous") is not None:
                parts.append(f"Your {name} is {_TREND_WORD[v['trend']]} ({v.get('previous')} → {v.get('value')}).")
        if not parts:
            parts.append("No major issues were found in your report.")
        parts.append("Please speak with your doctor.")
        return " ".join(parts)

    async def generate_summary(self, current_truth: CurrentTruthDTO, brief: dict, lang: str) -> dict:
        """Deterministic content per language (mr/hi/en). Unknown langs -> English."""
        if lang == "mr":
            return self._summary_mr(brief)
        if lang == "hi":
            return self._summary_hi(brief)
        return self._summary_en(brief)

    def _summary_mr(self, brief: dict) -> dict:
        what_we_found = []
        for lab in brief.get("recent_labs", []):
            trend = lab.get("trend")
            if trend == "up":
                what_we_found.append(f"तुमची {lab['test']} पातळी वाढली आहे.")
            elif trend == "down":
                what_we_found.append(f"तुमची {lab['test']} पातळी कमी झाली आहे.")
            elif lab.get("flag") in ("high", "low"):
                what_we_found.append(f"तुमची {lab['test']} पातळी सामान्यपेक्षा वेगळी आहे.")
        if not what_we_found:
            what_we_found.append("तुमच्या रिपोर्टमध्ये कोणतीही मोठी समस्या आढळली नाही.")

        medicines = [
            {
                "name": f"{m['name']} {m.get('dose') or ''}".strip(),
                "how_to_take": f"{m.get('frequency') or 'डॉक्टरांच्या सल्ल्यानुसार'} घ्या",
                "plain": "नियंत्रणासाठी",
            }
            for m in brief.get("active_medications", [])
        ]

        return {
            "greeting": "नमस्कार, तुमच्या रिपोर्टचा सोपा सारांश:",
            "what_we_found": what_we_found,
            "your_medicines": medicines,
            "what_to_watch": ["खूप थकवा, जास्त तहान किंवा चक्कर आल्यास डॉक्टरांना सांगा."],
            "next_steps": ["डॉक्टरांना भेटा आणि औषध नियमित घ्या."],
            "disclaimer": "हा सारांश माहितीसाठी आहे, वैद्यकीय सल्ल्याचा पर्याय नाही.",
        }

    def _summary_hi(self, brief: dict) -> dict:
        what_we_found = []
        for lab in brief.get("recent_labs", []):
            trend = lab.get("trend")
            if trend == "up":
                what_we_found.append(f"आपका {lab['test']} स्तर बढ़ा है।")
            elif trend == "down":
                what_we_found.append(f"आपका {lab['test']} स्तर कम हुआ है।")
            elif lab.get("flag") in ("high", "low"):
                what_we_found.append(f"आपका {lab['test']} स्तर सामान्य से अलग है।")
        if not what_we_found:
            what_we_found.append("आपकी रिपोर्ट में कोई बड़ी समस्या नहीं मिली।")

        medicines = [
            {
                "name": f"{m['name']} {m.get('dose') or ''}".strip(),
                "how_to_take": f"{m.get('frequency') or 'डॉक्टर की सलाह के अनुसार'} लें",
                "plain": "नियंत्रण के लिए",
            }
            for m in brief.get("active_medications", [])
        ]

        return {
            "greeting": "नमस्ते, आपकी रिपोर्ट का सरल सारांश:",
            "what_we_found": what_we_found,
            "your_medicines": medicines,
            "what_to_watch": ["बहुत थकान, ज़्यादा प्यास या चक्कर आने पर डॉक्टर को बताएं।"],
            "next_steps": ["डॉक्टर से मिलें और दवा नियमित रूप से लें।"],
            "disclaimer": "यह सारांश केवल जानकारी के लिए है, चिकित्सीय सलाह का विकल्प नहीं।",
        }

    def _summary_en(self, brief: dict) -> dict:
        what_we_found = []
        for lab in brief.get("recent_labs", []):
            if lab.get("trend") in ("up", "down"):
                what_we_found.append(f"Your {lab['test']} is {_TREND_WORD[lab['trend']]}.")
        if not what_we_found:
            what_we_found.append("No major issues found in your report.")
        return {
            "greeting": "Hello, here is a simple summary of your report:",
            "what_we_found": what_we_found,
            "your_medicines": [
                {
                    "name": f"{m['name']} {m.get('dose') or ''}".strip(),
                    "how_to_take": m.get("frequency") or "as advised by your doctor",
                    "plain": "for control",
                }
                for m in brief.get("active_medications", [])
            ],
            "what_to_watch": ["Tell your doctor if you feel very tired, thirsty, or dizzy."],
            "next_steps": ["See your doctor and take medicines regularly."],
            "disclaimer": "This summary is for information only and is not a substitute for medical advice.",
        }
