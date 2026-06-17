"""FHIR R4 Bundle export (B8) — Indian Patient Summary profile subset.

Framing export only: no ABDM gateway. Maps SETU brief + optional truth to a
valid FHIR Bundle JSON for interoperability demos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO


def brief_to_fhir_bundle(
    brief: DoctorBriefDTO,
    *,
    truth: CurrentTruthDTO | None = None,
    patient_display: str | None = None,
) -> dict[str, Any]:
    """Build a FHIR R4 Bundle with Composition + supporting resources."""
    now = datetime.now(timezone.utc).isoformat()
    patient_id = f"Patient/{brief.patient_id}"
    composition_id = f"Composition/{brief.brief_id}"
    org_id = "Organization/setu"

    entries: list[dict[str, Any]] = []

    entries.append(
        {
            "fullUrl": patient_id,
            "resource": {
                "resourceType": "Patient",
                "id": brief.patient_id,
                "name": [{"text": patient_display or "Patient"}],
            },
        }
    )

    entries.append(
        {
            "fullUrl": org_id,
            "resource": {
                "resourceType": "Organization",
                "id": "setu",
                "name": "SETU Health Bridge",
            },
        }
    )

    for i, med in enumerate(brief.active_medications):
        rid = f"MedicationStatement/{brief.brief_id}-med-{i}"
        entries.append(
            {
                "fullUrl": rid,
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": f"{brief.brief_id}-med-{i}",
                    "status": "active",
                    "subject": {"reference": patient_id},
                    "medicationCodeableConcept": {"text": med.name},
                    "dosage": [
                        {
                            "text": " ".join(
                                x for x in [med.dose, med.frequency] if x
                            )
                            or "As prescribed",
                        }
                    ],
                },
            }
        )

    for i, lab in enumerate(brief.recent_labs):
        rid = f"Observation/{brief.brief_id}-lab-{i}"
        value: dict[str, Any] = {}
        if isinstance(lab.value, (int, float)):
            value = {
                "valueQuantity": {
                    "value": lab.value,
                    "unit": lab.unit or "",
                }
            }
        else:
            value = {"valueString": str(lab.value)}
        entries.append(
            {
                "fullUrl": rid,
                "resource": {
                    "resourceType": "Observation",
                    "id": f"{brief.brief_id}-lab-{i}",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "laboratory",
                                }
                            ]
                        }
                    ],
                    "code": {"text": lab.test},
                    "subject": {"reference": patient_id},
                    "effectiveDateTime": lab.date,
                    "interpretation": (
                        [{"text": lab.flag}] if lab.flag and lab.flag != "normal" else []
                    ),
                    **value,
                },
            }
        )

    for i, cond in enumerate(brief.active_conditions):
        rid = f"Condition/{brief.brief_id}-cond-{i}"
        entries.append(
            {
                "fullUrl": rid,
                "resource": {
                    "resourceType": "Condition",
                    "id": f"{brief.brief_id}-cond-{i}",
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                    "code": {"text": cond.condition},
                    "subject": {"reference": patient_id},
                },
            }
        )

    section_refs: list[dict[str, str]] = []
    if brief.active_medications:
        section_refs.append(
            {
                "title": "Medications",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "10160-0",
                            "display": "History of Medication use",
                        }
                    ]
                },
                "entry": [
                    {"reference": f"MedicationStatement/{brief.brief_id}-med-{i}"}
                    for i in range(len(brief.active_medications))
                ],
            }
        )
    if brief.recent_labs:
        section_refs.append(
            {
                "title": "Laboratory",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "30954-2",
                            "display": "Relevant diagnostic tests/laboratory data",
                        }
                    ]
                },
                "entry": [
                    {"reference": f"Observation/{brief.brief_id}-lab-{i}"}
                    for i in range(len(brief.recent_labs))
                ],
            }
        )

    composition = {
        "resourceType": "Composition",
        "id": brief.brief_id,
        "status": "final",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "60591-5",
                    "display": "Patient summary Document",
                }
            ],
            "text": "Patient Summary",
        },
        "subject": {"reference": patient_id},
        "date": brief.generated_at.isoformat(),
        "author": [{"reference": org_id}],
        "title": "SETU Patient Summary",
        "section": section_refs,
    }
    if brief.chief_concern:
        composition["section"].insert(
            0,
            {
                "title": "Chief concern",
                "text": {"div": f"<div>{brief.chief_concern}</div>"},
            },
        )

    entries.insert(
        1,
        {
            "fullUrl": composition_id,
            "resource": composition,
        },
    )

    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": now,
        "identifier": {
            "system": "https://setu.health/fhir",
            "value": brief.brief_id,
        },
        "entry": entries,
    }
    if truth is not None:
        bundle["meta"] = {
            "tag": [
                {
                    "system": "https://setu.health/tags",
                    "code": "truth-generated-at",
                    "display": truth.generated_at.isoformat(),
                }
            ]
        }
    return bundle
