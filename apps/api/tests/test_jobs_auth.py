"""D-C3: GET /jobs/{id} and POST /jobs/{id}/retry require auth + patient ownership."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str = "patient") -> str:
    import jwt
    return jwt.encode(
        {"sub": sub, "aud": "authenticated", "app_metadata": {"role": role}},
        _SECRET, algorithm="HS256",
    )


def _bearer(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def _seed_job(jobs_store_module, job_id: str, patient_id: str, status: str = "failed") -> None:
    state = jobs_store_module.new_job_state(job_id, "doc_test", patient_id)
    state.status = status
    await jobs_store_module.save(state)


async def _seed_patient(session_factory, patient_id: str, user_id: str) -> None:
    from app.db.models import Patient
    async with session_factory() as db:
        db.add(Patient(id=patient_id, display_name="P", lang_pref="en",
                       patient_token=f"tok_{patient_id}", supabase_user_id=user_id))
        await db.commit()


async def test_get_job_no_auth_dev_mode_allowed(client):
    """In dev mode (SUPABASE_ENABLED=False) no auth required."""
    from app import jobs_store
    await _seed_job(jobs_store, "job_dev", "pat_dev")
    r = await client.get("/api/v1/jobs/job_dev")
    assert r.status_code == 200


async def test_get_job_owner_gets_200(client, session_factory, auth_enabled):
    from app import jobs_store
    await _seed_patient(session_factory, "pat_own", "u_own")
    await _seed_job(jobs_store, "job_own", "pat_own")
    r = await client.get("/api/v1/jobs/job_own", headers=_bearer(_token("u_own")))
    assert r.status_code == 200


async def test_get_job_non_owner_gets_403(client, session_factory, auth_enabled):
    from app import jobs_store
    await _seed_patient(session_factory, "pat_owner2", "u_owner2")
    await _seed_job(jobs_store, "job_403", "pat_owner2")
    r = await client.get("/api/v1/jobs/job_403", headers=_bearer(_token("u_other")))
    assert r.status_code == 403


async def test_retry_job_non_owner_gets_403(client, session_factory, auth_enabled):
    from app import jobs_store
    await _seed_patient(session_factory, "pat_retry", "u_retry_owner")
    await _seed_job(jobs_store, "job_retry403", "pat_retry", status="failed")
    r = await client.post("/api/v1/jobs/job_retry403/retry",
                          headers=_bearer(_token("u_retry_stranger")))
    assert r.status_code == 403
