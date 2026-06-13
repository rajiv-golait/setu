"""DB glue around the PURE reducer.

reducer.py itself has zero I/O. This module is the only place that loads claims,
runs reduce(), and upserts current_truth. Current Truth is always recomputed in
full (never patched incrementally).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Claim as ClaimRow
from app.db.models import CurrentTruth as TruthRow
from app.ids import new_id
from app.schemas.claims import Claim
from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.memory.reducer import reduce


async def load_claims(db: AsyncSession, patient_id: str) -> list[Claim]:
    rows = (
        await db.execute(
            select(ClaimRow).where(ClaimRow.patient_id == patient_id).order_by(ClaimRow.observed_at)
        )
    ).scalars().all()
    return [
        Claim(
            claim_id=r.id,
            type=r.claim_type,
            fields=r.fields,
            confidence=float(r.confidence),
            observed_at=r.observed_at,
            needs_review=r.needs_review,
        )
        for r in rows
    ]


async def recompute_current_truth(db: AsyncSession, patient_id: str) -> CurrentTruthDTO:
    """Load all claims, run the pure reducer, UPSERT current_truth, return the DTO."""
    claims = await load_claims(db, patient_id)
    entries = reduce(claims, confidence_threshold=settings.CONFIDENCE_THRESHOLD)

    # Full recompute: clear and rewrite this patient's derived rows.
    await db.execute(delete(TruthRow).where(TruthRow.patient_id == patient_id))
    now = datetime.now(timezone.utc)
    for e in entries:
        db.add(
            TruthRow(
                id=new_id("trt", 5),
                patient_id=patient_id,
                entry_type=e.entry_type,
                normalized_key=e.normalized_key,
                value=e.value,
                confidence=e.confidence,
                state=e.state,
                source_claim_ids=e.source_claim_ids,
                updated_at=now,
            )
        )
    await db.flush()
    return CurrentTruthDTO(patient_id=patient_id, entries=entries, generated_at=now)


async def load_current_truth(db: AsyncSession, patient_id: str) -> CurrentTruthDTO:
    """Read the persisted current_truth (without recomputing)."""
    rows = (
        await db.execute(select(TruthRow).where(TruthRow.patient_id == patient_id))
    ).scalars().all()
    entries = [
        CurrentTruthEntry(
            entry_type=r.entry_type,
            normalized_key=r.normalized_key,
            value=r.value,
            confidence=float(r.confidence) if r.confidence is not None else 0.0,
            state=r.state,
            source_claim_ids=r.source_claim_ids or [],
            updated_at=r.updated_at,
        )
        for r in rows
    ]
    entries.sort(key=lambda e: (e.entry_type, e.normalized_key))
    return CurrentTruthDTO(
        patient_id=patient_id,
        entries=entries,
        generated_at=datetime.now(timezone.utc),
    )
