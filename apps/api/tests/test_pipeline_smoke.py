"""Pipeline integration smoke test (mock providers).

document -> claims -> truth -> brief -> summary -> share, asserting schema-valid
output at each stage. Runs the orchestrator directly for determinism (BackgroundTasks
fire after the response in the test client).
"""
from __future__ import annotations

import os

import pytest

from app import jobs_store
from app.db.models import Document, Patient
from app.ids import new_id
from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO
from app.schemas.share import ShareSnapshotDTO
from app.schemas.summary import PatientSummaryDTO
from app.services import persistence
from app.services.memory.persistence import load_current_truth
from app.services.orchestrator import run_pipeline

pytestmark = pytest.mark.asyncio


async def _make_patient_and_doc(session_factory, tmp_path):
    # A real (empty) file on disk — the mock extractor ignores contents.
    fpath = os.path.join(tmp_path, "doc.jpg")
    with open(fpath, "wb") as f:
        f.write(b"fake-image-bytes")

    async with session_factory() as db:
        db.add(Patient(id="pat_s1", display_name="Test", lang_pref="mr", patient_token="tok_s1"))
        db.add(
            Document(
                id="doc_s1", patient_id="pat_s1", doc_type="prescription",
                storage_path=fpath, mime="image/jpeg", source="upload", status="pending",
            )
        )
        await db.commit()


async def test_full_pipeline_produces_valid_artifacts(session_factory, tmp_path):
    await _make_patient_and_doc(session_factory, tmp_path)

    job_id = new_id("job")
    await jobs_store.save(jobs_store.new_job_state(job_id, "doc_s1"))

    await run_pipeline(job_id, "doc_s1", "pat_s1")

    # Job completed through every stage.
    state = await jobs_store.load(job_id)
    assert state.status == "completed", state.error
    assert set(state.completed_stages) >= {"extraction", "validation", "memory", "brief"}
    assert "brief_id" in state.result

    async with session_factory() as db:
        # Current truth is schema-valid and non-empty.
        truth: CurrentTruthDTO = await load_current_truth(db, "pat_s1")
        assert len(truth.entries) > 0

        # Brief is schema-valid with computed flags.
        brief: DoctorBriefDTO = await persistence.latest_brief(db, "pat_s1")
        assert brief is not None
        assert brief.one_line
        # seeded diagnosis is low-confidence -> at least one needs_review flag
        assert any(f.type == "needs_review" for f in brief.flags)
        # seeded HbA1c trends up + high -> at least one abnormal_lab flag
        assert any(f.type == "abnormal_lab" for f in brief.flags)

        # Marathi summary is schema-valid.
        summary: PatientSummaryDTO = await persistence.latest_summary(db, "pat_s1", "mr")
        assert summary is not None
        assert summary.language == "mr"
        assert summary.disclaimer

        # Share snapshot embeds a valid brief + truth.
        token = state.result.get("share_token")
        assert token
        row = await persistence.get_share(db, token)
        snap = ShareSnapshotDTO.model_validate(row.snapshot_json)
        assert snap.read_only is True
        assert snap.brief.brief_id == brief.brief_id


async def test_hba1c_trend_is_up_in_truth(session_factory, tmp_path):
    """The two seeded HbA1c readings must yield a rising trend (regression guard)."""
    await _make_patient_and_doc(session_factory, tmp_path)
    job_id = new_id("job")
    await jobs_store.save(jobs_store.new_job_state(job_id, "doc_s1"))
    await run_pipeline(job_id, "doc_s1", "pat_s1")

    async with session_factory() as db:
        truth = await load_current_truth(db, "pat_s1")
        hba1c = next(e for e in truth.entries if e.normalized_key == "hba1c")
        assert hba1c.value["trend"] == "up"
        assert len(hba1c.value["history"]) == 2
