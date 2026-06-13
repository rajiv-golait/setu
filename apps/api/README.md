# SETU API (backend)

FastAPI backend for SETU — medical document intelligence. Photo of a prescription /
lab report → extracted **claims** → reduced **Current Truth** (patient memory) →
**Doctor Brief** → **QR share** with a doctor. Marathi patient summary + referral too.

**Default providers are `mock` — the whole stack runs with ZERO GPU.** Real AI
(Qwen3-VL extraction, MedGemma reasoning) is opt-in via env vars.

## Architecture at a glance

```
upload ─▶ ingestion ─▶ [orchestrator: extraction → validation → memory → brief → summary + share]
                                                          │
                              pure reducer (claims → Current Truth) ◀── append-only claims
                                                          │
                                       brief engine (model prose + code-computed flags)
```

- **Job state** lives in **Redis only** (`job:{id}`, 24h TTL) — never in Postgres.
- **Claims** are append-only; **Current Truth** is always recomputed by the pure
  reducer (`app/services/memory/reducer.py`) — never patched incrementally.
- **Safety flags** in the brief are computed by code, not the model.
- **Shares** embed an immutable snapshot — later uploads don't change a shared link.

## Run it (Docker, recommended)

```bash
cp .env.example .env          # from repo root
cd infra
make dev                      # db + redis + api (hot-reload), mock providers
make seed                     # demo patient: claims + truth + brief + summary + share
make gen-client               # export packages/contracts/openapi.json
```

API at http://localhost:8000 — docs at `/docs`, schema at `/openapi.json`.

### Demo mode

Set `DEMO_MODE=true`. `GET /patients/{id}/memory` and `/brief` then serve the
seeded patient (`SEED_PATIENT_ID`) instantly, no pipeline.

## Run tests (no Docker needed)

```bash
cd apps/api
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q                                            # uses in-memory sqlite + fake redis
```

Test suite (all GPU-free, mock providers):
- `test_reducer.py` — reducer rules (latest-wins, tie-break, trend, conflict,
  possibly_discontinued, confidence gate, provenance, idempotence). **Highest priority.**
- `test_validation.py` — plausibility ranges, required fields, confidence gating.
- `test_brief_flags.py` — flags are code-computed (abnormal_lab/needs_review/conflict/missing_data).
- `test_pipeline_smoke.py` — full pipeline → schema-valid artifacts per stage.
- `test_api_e2e.py` — brief → share → public snapshot (the demo centerpiece).
- `test_contract.py` — committed `openapi.json` matches the live schema (no drift).

## Switching to real AI (Day 3, GPU box)

```bash
docker compose -f docker-compose.yml -f docker-compose.models.yml up   # vLLM Qwen + MedGemma
# then set:
EXTRACTION_PROVIDER=qwen      QWEN_ENDPOINT=http://qwen:8000/v1
REASONING_PROVIDER=medgemma   MEDGEMMA_ENDPOINT=http://medgemma:8000/v1
```

Extraction routing chain: **qwen → cloud → seeded mock** (never fails silently).
Reasoning falls back to deterministic templates if the model output is invalid.

## Layout

```
app/
  config.py            all env vars (pydantic-settings)
  errors.py            error envelope + handlers
  main.py              app, CORS, router mount, lifespan
  db/                  base, async session, ORM models
  schemas/             Pydantic DTOs (the API contract)
  routers/             thin controllers, one per resource
  services/
    extraction/        ExtractorProvider: mock | qwen | cloud + routing factory
    memory/            reducer (PURE) + normalize + persistence glue
    reasoning/         ReasonerProvider: mock | medgemma + factory
    brief.py           brief engine (deterministic flags)
    summary.py         Marathi patient summary
    sharing.py         snapshot + QR (segno)
    validation.py      schema + plausibility + confidence gating
    orchestrator.py    pipeline runner (BackgroundTasks) + Redis job state
  seed/                demo patient fixtures + seed script
alembic/               migrations
tests/
scripts/export_openapi.py
```
