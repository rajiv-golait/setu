"""DB persistence helpers for claims, extractions, briefs, summaries, shares.

Thin functions used by the orchestrator and routers so business logic stays out
of controllers.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Brief as BriefRow
from app.db.models import Claim as ClaimRow
from app.db.models import Consent as ConsentRow
from app.db.models import Extraction as ExtractionRow
from app.db.models import Share as ShareRow
from app.db.models import Summary as SummaryRow
from app.ids import new_id, new_token
from app.schemas.brief import DoctorBriefDTO
from app.schemas.claims import Claim, ClaimsJSON
from app.schemas.summary import PatientSummaryDTO
from app.services.memory.normalize import normalize_key
from app.services.memory.reducer import grouping_key

_DEFAULT_SHARE_TTL = 7 * 24 * 3600  # 7 days


async def persist_extraction(db: AsyncSession, claims_json: ClaimsJSON) -> None:
    db.add(
        ExtractionRow(
            id=new_id("ext", 5),
            document_id=claims_json.document_id,
            provider=claims_json.provider,
            raw_json=claims_json.model_dump(mode="json"),
            overall_confidence=claims_json.overall_confidence,
        )
    )
    await db.flush()


async def persist_claims(
    db: AsyncSession, patient_id: str, document_id: str, claims: list[Claim]
) -> None:
    """Append claims (append-only). normalized_key set here for reducer grouping.

    Claim IDs from extractors are ephemeral (models often reuse clm_001, clm_002);
    always assign fresh server IDs for the DB primary key.
    """
    for c in claims:
        db.add(
            ClaimRow(
                id=new_id("clm", 5),
                patient_id=patient_id,
                document_id=document_id,
                claim_type=c.type,
                normalized_key=grouping_key(c),
                fields=c.fields,
                confidence=c.confidence,
                observed_at=c.observed_at,
                needs_review=c.needs_review,
            )
        )
    await db.flush()


async def persist_brief(db: AsyncSession, brief: DoctorBriefDTO) -> None:
    db.add(
        BriefRow(
            id=brief.brief_id,
            patient_id=brief.patient_id,
            brief_json=brief.model_dump(mode="json"),
            model=brief.model,
            generated_at=brief.generated_at,
        )
    )
    await db.flush()


async def latest_brief(db: AsyncSession, patient_id: str) -> DoctorBriefDTO | None:
    row = (
        await db.execute(
            select(BriefRow)
            .where(BriefRow.patient_id == patient_id)
            .order_by(BriefRow.generated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return DoctorBriefDTO.model_validate(row.brief_json) if row else None


async def persist_summary(db: AsyncSession, summary: PatientSummaryDTO) -> None:
    db.add(
        SummaryRow(
            id=summary.summary_id,
            patient_id=summary.patient_id,
            lang=summary.language,
            summary_json=summary.model_dump(mode="json"),
            model=summary.model,
            generated_at=summary.generated_at,
        )
    )
    await db.flush()


async def latest_summary(
    db: AsyncSession, patient_id: str, lang: str
) -> PatientSummaryDTO | None:
    row = (
        await db.execute(
            select(SummaryRow)
            .where(SummaryRow.patient_id == patient_id, SummaryRow.lang == lang)
            .order_by(SummaryRow.generated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return PatientSummaryDTO.model_validate(row.summary_json) if row else None


async def create_share(
    db: AsyncSession,
    patient_id: str,
    snapshot: dict,
    expires_in: int | None,
    token: str | None = None,
) -> ShareRow:
    now = datetime.now(timezone.utc)
    ttl = expires_in if expires_in is not None else _DEFAULT_SHARE_TTL
    row = ShareRow(
        id=new_id("shr", 3),
        patient_id=patient_id,
        token=token or new_token(10),
        snapshot_json=snapshot,
        view_count=0,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl),
    )
    db.add(row)
    await db.flush()
    return row


async def get_share(db: AsyncSession, token: str) -> ShareRow | None:
    return (
        await db.execute(select(ShareRow).where(ShareRow.token == token))
    ).scalar_one_or_none()


async def replace_reminders(
    db: AsyncSession, patient_id: str, items: list[dict]
) -> None:
    """Replace a patient's reminder schedule with the freshly computed one.

    Reminders are a pure derivation of current_truth (like the brief), so we
    recompute + replace rather than patch — never accumulate stale entries.
    """
    from sqlalchemy import delete

    from app.db.models import Reminder as ReminderRow

    await db.execute(delete(ReminderRow).where(ReminderRow.patient_id == patient_id))
    for item in items:
        schedule = {
            k: v
            for k, v in item.items()
            if k not in ("type", "label", "source_claim_id", "needs_confirmation")
        }
        db.add(
            ReminderRow(
                id=new_id("rem", 5),
                patient_id=patient_id,
                reminder_type=item["type"],
                label=item["label"],
                schedule=schedule,
                source_claim_id=item.get("source_claim_id"),
                needs_confirmation=bool(item.get("needs_confirmation", False)),
            )
        )
    await db.flush()


async def record_consent(
    db: AsyncSession, patient_id: str, purpose: str, consent_text: str, lang: str, channel: str
) -> ConsentRow:
    row = ConsentRow(
        id=new_id("con", 5),
        patient_id=patient_id,
        purpose=purpose,
        consent_text=consent_text,
        lang=lang,
        channel=channel,
        granted_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    return row


async def has_consent(db: AsyncSession, patient_id: str, purpose: str) -> bool:
    row = (
        await db.execute(
            select(ConsentRow.id)
            .where(ConsentRow.patient_id == patient_id, ConsentRow.purpose == purpose)
            .limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def revoke_consent(db: AsyncSession, patient_id: str, purpose: str) -> bool:
    """Delete consent row for purpose. Returns True if a row was removed."""
    from sqlalchemy import delete

    result = await db.execute(
        delete(ConsentRow).where(
            ConsentRow.patient_id == patient_id,
            ConsentRow.purpose == purpose,
        )
    )
    await db.flush()
    return result.rowcount > 0


# re-export so callers can normalize without importing the deep path
_ = normalize_key
