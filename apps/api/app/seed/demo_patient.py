"""Seed the demo patient. Run via `make seed`.

Inserts:
  - patient pat_demo / token tok_demo
  - 3 documents (prescription, lab report, discharge summary)
  - ~8 claims (2 meds, 3 labs incl. HbA1c trend, 1 dx low-conf, 1 allergy, 1 vital)
  - current_truth recomputed by the REAL reducer (so it matches production exactly)
  - a Doctor Brief (real brief engine + deterministic flags)
  - a Marathi Patient Summary
  - a share with the fixed token shr_demo_token, expiring 7 days out

Idempotent: wipes the demo patient's rows first, then re-seeds.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete

from app.db.models import (
    Brief,
    Claim,
    CurrentTruth,
    Document,
    Patient,
    Share,
    Summary,
)
from app.db.session import SessionLocal
from app.ids import new_id
from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO
from app.seed.fixtures import (
    DEMO_DOCUMENTS,
    DEMO_PATIENT_ID,
    DEMO_PATIENT_TOKEN,
    DEMO_SHARE_TOKEN,
    demo_claims,
)
from app.services.brief import build_brief
from app.services.memory.persistence import recompute_current_truth
from app.services.reasoning.mock import MockReasoner
from app.services.sharing import build_snapshot
from app.services.summary import build_summary


async def _wipe(db, patient_id: str) -> None:
    for model in (Share, Summary, Brief, CurrentTruth, Claim, Document):
        await db.execute(delete(model).where(model.patient_id == patient_id))
    await db.execute(delete(Patient).where(Patient.id == patient_id))
    await db.flush()


async def seed() -> None:
    async with SessionLocal() as db:
        await _wipe(db, DEMO_PATIENT_ID)

        # Patient.
        db.add(
            Patient(
                id=DEMO_PATIENT_ID,
                display_name="62F",
                lang_pref="mr",
                patient_token=DEMO_PATIENT_TOKEN,
            )
        )

        # Documents.
        for d in DEMO_DOCUMENTS:
            db.add(
                Document(
                    id=d["id"],
                    patient_id=DEMO_PATIENT_ID,
                    doc_type=d["doc_type"],
                    storage_path=f"/data/seed/{d['id']}",
                    mime=d["mime"],
                    source="seed",
                    status="extracted",
                )
            )

        # Claims (append-only; normalized_key via the reducer's grouping logic).
        from app.schemas.claims import Claim as ClaimSchema
        from app.services.memory.reducer import grouping_key

        for c in demo_claims(DEMO_PATIENT_ID):
            schema = ClaimSchema(
                claim_id=c["claim_id"],
                type=c["type"],
                fields=c["fields"],
                confidence=c["confidence"],
                observed_at=date.fromisoformat(c["observed_at"]) if c.get("observed_at") else None,
                needs_review=c.get("needs_review", False),
            )
            db.add(
                Claim(
                    id=c["claim_id"],
                    patient_id=DEMO_PATIENT_ID,
                    document_id=c["document_id"],
                    claim_type=c["type"],
                    normalized_key=grouping_key(schema),
                    fields=c["fields"],
                    confidence=c["confidence"],
                    observed_at=schema.observed_at,
                    needs_review=c.get("needs_review", False),
                )
            )
        await db.flush()

        # Current Truth — recomputed by the REAL reducer.
        truth: CurrentTruthDTO = await recompute_current_truth(db, DEMO_PATIENT_ID)

        # Brief — real engine + deterministic flags.
        reasoner = MockReasoner()
        source_docs = [d["id"] for d in DEMO_DOCUMENTS]
        brief: DoctorBriefDTO = await build_brief(DEMO_PATIENT_ID, truth, reasoner, source_docs)
        db.add(
            Brief(
                id=brief.brief_id,
                patient_id=DEMO_PATIENT_ID,
                brief_json=brief.model_dump(mode="json"),
                model=brief.model,
                generated_at=brief.generated_at,
            )
        )

        # Marathi Summary.
        summary = await build_summary(DEMO_PATIENT_ID, truth, brief, reasoner, lang="mr")
        db.add(
            Summary(
                id=summary.summary_id,
                patient_id=DEMO_PATIENT_ID,
                lang="mr",
                summary_json=summary.model_dump(mode="json"),
                model=summary.model,
                generated_at=summary.generated_at,
            )
        )

        # Share with the fixed demo token.
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=7)
        snapshot = build_snapshot(
            share_id=new_id("shr", 3),
            token=DEMO_SHARE_TOKEN,
            created_at=now,
            expires_at=expires,
            patient_ref="Patient (62F)",
            brief=brief,
            current_truth=truth,
        )
        db.add(
            Share(
                id=snapshot.share_id,
                patient_id=DEMO_PATIENT_ID,
                token=DEMO_SHARE_TOKEN,
                snapshot_json=snapshot.model_dump(mode="json"),
                view_count=0,
                created_at=now,
                expires_at=expires,
            )
        )

        await db.commit()
        print(f"Seeded {DEMO_PATIENT_ID}: {len(truth.entries)} truth entries, brief {brief.brief_id}, share {DEMO_SHARE_TOKEN}")


if __name__ == "__main__":
    asyncio.run(seed())
