"""Upload deduplication and queue-only pipeline scheduling."""
from __future__ import annotations

import io

import pytest

from app.services.job_queue import QUEUE_KEY, schedule_pipeline

pytestmark = pytest.mark.asyncio


async def _patient_with_consent(client, session_factory, pid):
    from app.db.models import Patient

    async with session_factory() as db:
        db.add(Patient(id=pid, display_name="T", lang_pref="mr", patient_token=f"tok_{pid}"))
        await db.commit()
    r = await client.post(
        "/api/v1/consent",
        json={"patient_id": pid, "purpose": "document_processing", "lang": "mr", "channel": "web"},
    )
    assert r.status_code == 201, r.text


def _file(content: bytes = b"raw-bytes-here", name: str = "rx.jpg"):
    return {"file": (name, io.BytesIO(content), "image/jpeg")}


async def test_duplicate_upload_returns_same_document(client, session_factory, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "STORAGE_PATH", str(tmp_path))
    pid = "pat_dedup1"
    await _patient_with_consent(client, session_factory, pid)

    r1 = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    assert r1.status_code == 202, r1.text
    body1 = r1.json()
    assert body1["duplicate"] is False

    r2 = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    assert r2.status_code == 202, r2.text
    body2 = r2.json()
    assert body2["duplicate"] is True
    assert body2["document_id"] == body1["document_id"]


async def test_batch_upload_accepts_multiple_files(client, session_factory, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "STORAGE_PATH", str(tmp_path))
    pid = "pat_batch1"
    await _patient_with_consent(client, session_factory, pid)

    files = [
        ("files", ("a.jpg", io.BytesIO(b"file-a"), "image/jpeg")),
        ("files", ("b.jpg", io.BytesIO(b"file-b"), "image/jpeg")),
    ]
    r = await client.post(
        "/api/v1/documents/batch",
        files=files,
        data={"patient_id": pid},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["document_id"] != body["items"][1]["document_id"]


async def test_schedule_pipeline_skips_duplicate_enqueue(_patch_redis):
    fake = _patch_redis
    first = await schedule_pipeline("job_1", "doc_1", "pat_1")
    second = await schedule_pipeline("job_2", "doc_1", "pat_1")
    assert first is True
    assert second is False
    assert len(fake._lists.get(QUEUE_KEY, [])) == 1
