"""Pipeline orchestrator. Runs via FastAPI BackgroundTasks (NOT Celery/ARQ).

Stages (in order):  extraction -> validation -> memory -> explanation -> brief -> share

If reply_chat_id is given (Telegram), the explanation + brief link are sent back
to that chat once the brief is ready.

Stage isolation rules:
  - Redis job status updated at the START and END of each stage.
  - On stage failure: set failed_at, preserve all prior results, retryable=True.
  - Never lose completed work to a downstream failure.
  - claims / current_truth / brief are persisted to DB at their stages.

The job opens its OWN db session (it runs after the request returns).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app import jobs_store
from app.config import settings
from app.db.models import Document, Patient
from app.db.session import SessionLocal
from app.errors import EXTRACTION_FAILED, INTERNAL, REASONING_FAILED
from app.schemas.claims import ClaimsJSON
from app.schemas.jobs import STAGES, JobStatusDTO
from app.seed.fixtures import BRIEF_HANDOFF_MSG
from app.services import persistence
from app.services import telegram as telegram_service
from app.services.brief import build_brief
from app.services.explanation import generate_explanation
from app.services.extraction.factory import extract_with_fallback
from app.services.memory import persistence as memory_persistence
from app.services.reasoning.factory import get_reasoner
from app.services.sharing import build_snapshot, make_qr_svg, share_url
from app.services.validation import validate_claims

logger = logging.getLogger("setu.orchestrator")


async def _set_stage_start(state: JobStatusDTO, stage: str) -> None:
    state.status = "running"
    state.stage = stage
    state.progress = round(STAGES.index(stage) / len(STAGES), 2)
    await jobs_store.save(state)


async def _set_stage_done(state: JobStatusDTO, stage: str) -> None:
    if stage not in state.completed_stages:
        state.completed_stages.append(stage)
    state.progress = round(len(state.completed_stages) / len(STAGES), 2)
    await jobs_store.save(state)


async def _fail(state: JobStatusDTO, stage: str, code: str, message: str) -> None:
    state.status = "failed"
    state.failed_at = stage
    state.error = {"code": code, "message": message, "details": {"stage": stage}, "retryable": True}
    await jobs_store.save(state)
    logger.warning("job %s failed at %s: %s", state.job_id, stage, message)


async def run_pipeline(
    job_id: str,
    document_id: str,
    patient_id: str,
    reply_chat_id: str | None = None,
) -> None:
    """Full pipeline. Each stage is isolated; prior work is preserved on failure.

    If reply_chat_id is set, the explanation + brief link are sent to that
    Telegram chat once the brief is generated.
    """
    state = await jobs_store.load(job_id) or jobs_store.new_job_state(job_id, document_id)

    async with SessionLocal() as db:
        # Resolve the document (for file path + mime).
        doc = (
            await db.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if doc is None:
            await _fail(state, "extraction", INTERNAL, "document not found")
            return

        # Patient language preference (default mr) for the explanation.
        patient = (
            await db.execute(select(Patient).where(Patient.id == patient_id))
        ).scalar_one_or_none()
        lang = (patient.lang_pref if patient and patient.lang_pref else "mr")

        # --- STAGE: extraction ---
        try:
            await _set_stage_start(state, "extraction")
            claims_json: ClaimsJSON = await extract_with_fallback(
                doc.storage_path, doc.mime or "application/octet-stream",
                patient_id=patient_id, document_id=document_id,
            )
            await persistence.persist_extraction(db, claims_json)
            doc.status = "extracted"
            await db.commit()
            await _set_stage_done(state, "extraction")
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            await _fail(state, "extraction", EXTRACTION_FAILED, str(exc))
            return

        # --- STAGE: validation ---
        try:
            await _set_stage_start(state, "validation")
            result = validate_claims(claims_json, settings.CONFIDENCE_THRESHOLD)
            await _set_stage_done(state, "validation")
        except Exception as exc:  # noqa: BLE001
            await _fail(state, "validation", INTERNAL, str(exc))
            return

        # --- STAGE: memory (persist claims + recompute current truth) ---
        try:
            await _set_stage_start(state, "memory")
            await persistence.persist_claims(db, patient_id, document_id, result.claims)
            truth = await memory_persistence.recompute_current_truth(db, patient_id)
            await db.commit()
            await _set_stage_done(state, "memory")
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            await _fail(state, "memory", INTERNAL, str(exc))
            return

        reasoner = get_reasoner()
        source_docs = await _source_documents(db, patient_id)

        # --- STAGE: explanation (caregiver-facing plain-language reply) ---
        explanation_text = ""
        try:
            await _set_stage_start(state, "explanation")
            explanation_text = await generate_explanation(
                truth, lang, claims_json.document_type, reasoner,
                overall_confidence=claims_json.overall_confidence,
            )
            await jobs_store.save_explanation(
                document_id, explanation_text, float(claims_json.overall_confidence)
            )
            state.result["explanation"] = explanation_text
            await _set_stage_done(state, "explanation")
        except Exception as exc:  # noqa: BLE001
            await _fail(state, "explanation", REASONING_FAILED, str(exc))
            return

        # --- STAGE: brief ---
        try:
            await _set_stage_start(state, "brief")
            brief = await build_brief(patient_id, truth, reasoner, source_docs)
            await persistence.persist_brief(db, brief)
            await db.commit()
            state.result["brief_id"] = brief.brief_id
            await _set_stage_done(state, "brief")
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            await _fail(state, "brief", REASONING_FAILED, str(exc))
            return

        # --- STAGE: share (tokenized brief link; failures here are non-fatal) ---
        brief_token: str | None = None
        try:
            await _set_stage_start(state, "share")
            snapshot = build_snapshot(
                share_id="shr_pending", token="pending",
                created_at=datetime.now(timezone.utc), expires_at=None,
                patient_ref=_patient_ref(patient_id), brief=brief, current_truth=truth,
            )
            row = await persistence.create_share(
                db, patient_id, snapshot.model_dump(mode="json"), expires_in=None
            )
            await db.commit()
            brief_token = row.token
            state.result["share_token"] = row.token
            await _set_stage_done(state, "share")
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.warning("share stage failed (non-fatal): %s", exc)

        # --- Telegram reply: explanation + brief link (non-fatal) ---
        if reply_chat_id:
            try:
                if explanation_text:
                    await telegram_service.send_message(reply_chat_id, explanation_text)
                if brief_token:
                    brief_url = f"{settings.BRIEF_BASE_URL.rstrip('/')}/brief/{brief_token}"
                    await telegram_service.send_message(
                        reply_chat_id, BRIEF_HANDOFF_MSG.format(url=brief_url)
                    )
            except Exception as exc:  # noqa: BLE001 — reply failure must not fail the job
                logger.warning("telegram reply failed (non-fatal): %s", exc)

        # --- done ---
        state.status = "completed"
        state.stage = None
        state.progress = 1.0
        await jobs_store.save(state)


async def _source_documents(db, patient_id: str) -> list[str]:
    rows = (
        await db.execute(select(Document.id).where(Document.patient_id == patient_id))
    ).scalars().all()
    return list(rows)


def _patient_ref(patient_id: str) -> str:
    return "Patient"


# expose QR + url helpers for the share router convenience
make_share_qr = make_qr_svg
build_share_url = share_url
