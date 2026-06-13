# SETU — Engineering Build Plan & Two-Agent Coordination

**From:** Staff Engineer / TPM
**To:** Claude Code (Backend) · Claude Design (Frontend)
**Goal:** Working, demo-reliable MVP by **June 20** (4-day window).
**Architecture:** LOCKED. This document does not redesign it — it decomposes, sequences, and coordinates it.

## The one principle that governs this whole plan

> **The product is the brief + memory + QR share. Make that demo-solid on _seeded claims_ BEFORE extraction is real.**

Extraction (especially handwriting) is the riskiest, slowest-to-stabilise part. So we **invert the obvious build order**: stub extraction with seeded/mock claims on Day 1, build the entire memory → brief → summary → share pipeline against that, get it bulletproof by end of Day 2, and only then swap in the real Qwen3-VL extractor. If extraction misbehaves on demo day, the core still works.

**Two operating rules for every decision below:** when ambiguous, choose the simpler implementation; if a feature threatens the demo-solid core, cut it (see the cut list in Part 9).

---

# PART 1 — System decomposition

## 1.1 Modules (bounded, single-responsibility)

| # | Module | Owner | Responsibility | Depends on |
|---|---|---|---|---|
| M1 | **Contracts & Types** | Backend (shared) | OpenAPI spec, Pydantic DTOs, JSON schemas, generated TS client | — (built first) |
| M2 | **Ingestion** | Backend | Accept upload, store file, create `document` + `job`, kick pipeline | M1 |
| M3 | **Extraction** | Backend | Provider-abstracted image/PDF → **Claims JSON** (Qwen3-VL-8B / cloud fallback / **mock**) | M1 |
| M4 | **Validation** | Backend | Schema + plausibility + confidence-gating on claims | M3 |
| M5 | **Memory** | Backend | Claims → **Reducer** → **Current Truth** (deterministic, replayable) | M4 |
| M6 | **Brief Engine** | Backend | Current Truth → **Doctor Brief JSON** (MedGemma-4B) | M5 |
| M7 | **Summary** | Backend | Current Truth + Brief → **Marathi Patient Summary JSON** (MedGemma-4B) | M6 |
| M8 | **Sharing** | Backend | Brief + Truth → **Snapshot** → token + link + QR | M6 |
| M9 | **Referral** | Backend | Brief → specialist referral record | M6 |
| M10 | **Orchestration** | Backend | Pipeline runner + job status (Redis), stage isolation, retries | M2–M9 |
| F1 | **PWA Shell** | Frontend | Next.js PWA, layout, nav, install, offline shell | M1 |
| F2 | **Upload Flow** | Frontend | Capture/upload, job polling, progress UI | M1 (mock) |
| F3 | **Brief View** | Frontend | Render Doctor Brief, flags, source provenance | M1 (mock) |
| F4 | **Summary View** | Frontend | Render Marathi summary, plain-language meds | M1 (mock) |
| F5 | **Memory Timeline** | Frontend | Longitudinal Current Truth + history view | M1 (mock) |
| F6 | **Share/QR** | Frontend | Create share, show QR, public read-only snapshot page | M1 (mock) |
| F7 | **Referral UI** | Frontend | Specialist referral form + confirmation | M1 (mock) |

## 1.2 The document pipeline (locked flow, with stage isolation)

```
Upload ─▶ [M2 Ingestion] ─▶ job:created
                              │
              ┌───────────────▼────────────────┐
              │ [M10 Orchestrator] async runner │  ← Redis job status, each stage isolated + retryable
              └───────────────┬────────────────┘
   PDF/Image ─▶ [M3 Extraction] ─▶ Claims JSON ─▶ [M4 Validation] ─▶ validated claims
                                                                          │
                                                       persist claims ─────▼──── [M5 Memory Reducer]
                                                                          │            │
                                                                  Current Truth ◀──────┘ (recompute, idempotent)
                                                                          │
                                              ┌───────────────────────────┼───────────────────────┐
                                              ▼                           ▼                       ▼
                                       [M6 Brief Engine]          [M7 Summary (mr)]        [M8 Snapshot/QR]
                                              │                           │                       │
                                         Doctor Brief            Patient Summary           Share link + QR
```

**Stage isolation is non-negotiable for demo reliability:** if Extraction succeeds but Brief fails, the job records `failed_at: brief`, preserves claims + current truth, and exposes a retry — we never lose good work to a downstream hiccup.

## 1.3 Identity model (kept deliberately minimal — no accounts)

No doctor accounts, no real auth. A **patient** is an anonymous record created on first use; the client holds an opaque `patient_token` (localStorage). Shares are accessed via an unguessable `share_token` (public, read-only, expiring). That's the entire identity surface for the MVP. Don't build more.

---

# PART 2 — Repository structure (monorepo)

```
setu/
├── apps/
│   ├── api/                      # FastAPI backend (Claude Code)
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app, router mount, CORS, lifespan
│   │   │   ├── config.py         # pydantic-settings: all env vars in one place
│   │   │   ├── db/
│   │   │   │   ├── session.py     # SQLAlchemy engine/session
│   │   │   │   ├── base.py
│   │   │   │   └── models.py      # ORM models (Part 6)
│   │   │   ├── schemas/           # Pydantic DTOs == API contracts (Part 5)
│   │   │   │   ├── claims.py
│   │   │   │   ├── brief.py
│   │   │   │   ├── summary.py
│   │   │   │   ├── share.py
│   │   │   │   ├── memory.py
│   │   │   │   └── jobs.py
│   │   │   ├── routers/           # one file per resource
│   │   │   │   ├── patients.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── memory.py
│   │   │   │   ├── brief.py
│   │   │   │   ├── summary.py
│   │   │   │   ├── shares.py
│   │   │   │   └── referrals.py
│   │   │   ├── services/          # business logic (the modules)
│   │   │   │   ├── ingestion.py
│   │   │   │   ├── extraction/
│   │   │   │   │   ├── base.py     # ExtractorProvider interface
│   │   │   │   │   ├── qwen.py     # Qwen3-VL-8B impl
│   │   │   │   │   ├── cloud.py    # cloud frontier fallback impl
│   │   │   │   │   └── mock.py     # seeded/mock impl (DEFAULT in dev)
│   │   │   │   ├── validation.py
│   │   │   │   ├── memory/
│   │   │   │   │   ├── reducer.py  # PURE function: claims -> current truth (Part 6/15)
│   │   │   │   │   └── normalize.py
│   │   │   │   ├── reasoning/
│   │   │   │   │   ├── base.py     # ReasonerProvider interface
│   │   │   │   │   ├── medgemma.py
│   │   │   │   │   └── mock.py
│   │   │   │   ├── brief.py
│   │   │   │   ├── summary.py
│   │   │   │   ├── sharing.py      # snapshot + QR
│   │   │   │   └── orchestrator.py # pipeline runner + job status
│   │   │   └── seed/
│   │   │       └── demo_patient.py # seeded claims + cached brief/summary/QR
│   │   ├── alembic/               # migrations
│   │   ├── tests/                 # reducer unit tests, pipeline smoke, contract tests
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/                       # Next.js PWA (Claude Design)
│       ├── app/                   # App Router
│       │   ├── (patient)/
│       │   │   ├── page.tsx        # home / upload
│       │   │   ├── brief/page.tsx
│       │   │   ├── summary/page.tsx
│       │   │   ├── memory/page.tsx
│       │   │   └── referral/page.tsx
│       │   └── share/[token]/page.tsx  # PUBLIC read-only snapshot
│       ├── components/            # shadcn/ui + feature components
│       ├── lib/
│       │   ├── api-client/         # GENERATED from OpenAPI (do not hand-edit)
│       │   ├── mocks/              # MSW handlers mirroring contracts
│       │   └── hooks/              # useJobPolling, useBrief, etc.
│       ├── public/                # manifest.json, icons, service worker
│       ├── package.json
│       └── Dockerfile
├── packages/
│   └── contracts/                 # SINGLE SOURCE OF TRUTH for cross-team types
│       ├── openapi.json           # exported from FastAPI (CI-checked)
│       └── json-schemas/          # Claims, Brief, Summary, Snapshot (Part 14)
├── infra/
│   ├── docker-compose.yml         # db, redis, api, web (models via env endpoints)
│   ├── docker-compose.models.yml  # optional: vLLM Qwen, MedGemma (GPU box only)
│   └── Makefile                   # make dev / make seed / make gen-client / make test
├── docs/
│   └── BUILD_PLAN.md              # this file
├── .github/workflows/ci.yml       # lint, test, build, openapi-drift check
└── .env.example
```

**Why this structure:** the `packages/contracts/` directory is the integration contract. Backend exports `openapi.json`; frontend generates its typed client from it. CI fails if the committed `openapi.json` drifts from the live FastAPI schema. This single mechanism is what lets the two agents work in parallel with near-zero integration risk.

---

# PART 3 — Frontend tasks (Claude Design)

**Stack:** Next.js (App Router, PWA) · TypeScript · Tailwind · shadcn/ui. **Works entirely against mocks (MSW) from hour one** — never blocked on backend.

### F1 — PWA shell & foundation `[Day 1]`
- Next.js + Tailwind + shadcn/ui init; `manifest.json`, icons, service worker (installable, offline shell).
- App layout, bottom-nav (Home/Memory/Share), loading & error boundaries.
- Generate typed API client from `packages/contracts/openapi.json`; wire MSW mock handlers mirroring every endpoint.
- **DoD:** app installs as PWA, renders shell, all screens reachable with mock data.

### F2 — Upload & processing flow `[Day 1 mock → Day 2 real]`
- Camera capture + file picker (image/PDF), client-side size/type guard, preview.
- `POST /documents` → receive `job_id` → **poll `GET /jobs/{id}`** with a friendly staged progress UI ("Reading… Understanding… Building brief…").
- Handle every job state: queued, running(stage), completed, failed(stage)+retry.
- **DoD:** upload a file, watch real staged progress, land on the brief when done.

### F3 — Doctor Brief view `[Day 1 mock → polish Day 2]`
- Render **Doctor Brief JSON**: one-line patient summary, chief concern, active meds, recent labs (with high/low flags + trend arrows), conditions, allergies, timeline, **flags** (highlighted), suggested questions.
- Show **provenance**: each item links to its source document; show confidence / "needs review" badges.
- **DoD:** a complete brief renders cleanly on mobile; flags and low-confidence items are visually unmistakable.

### F4 — Marathi Patient Summary view `[Day 3]`
- Render **Patient Summary JSON** in Marathi: what we found, your medicines (plain how-to-take), what to watch, next steps, disclaimer.
- Language toggle (mr/en) if both present; Devanagari-safe font + sizing.
- **DoD:** Marathi summary is readable, plain, and renders without layout/script breakage.

### F5 — Memory timeline `[Day 2 mock → Day 3 real]`
- Render **Current Truth**: active medications, latest labs with history sparkline, conditions, allergies, documents list.
- Conflict/needs-review entries clearly flagged (never silently shown as fact).
- **DoD:** longitudinal state is legible; adding a new document visibly updates the timeline.

### F6 — Share / QR `[Day 2 — part of demo-solid core]`
- "Share with doctor" → `POST /shares` → show **QR** (large, scannable) + copyable link + expiry.
- Public `/share/[token]` page: read-only snapshot of brief + current truth, no app chrome, loads fast, works for an unauthenticated doctor on their own phone.
- **DoD:** generate a QR, scan it on a second device, see the read-only brief. This is a demo centerpiece — make it flawless.

### F7 — Referral flow `[Day 3]`
- From a brief, "Refer to specialist" → pick specialty + auto-filled reason from brief → `POST /referrals` → confirmation + (optionally) a shareable referral snapshot.
- **DoD:** create a referral from a brief and see confirmation.

### Cross-cutting (all days)
Empty/loading/error states for every screen; mobile-first; optimistic where safe; **a global `DEMO_MODE` banner-free path** that loads the seeded patient instantly.

---

# PART 4 — Backend tasks (Claude Code)

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Alembic · Redis · Docker. **Build the core on seeded claims first; make AI real second.**

### B0 — Contracts & foundation `[Day 1 — BLOCKS NOTHING ELSE UNTIL DONE]`
- Monorepo skeleton, `docker-compose` (db/redis/api/web), `config.py` (all env), CORS.
- All **Pydantic DTOs** (Claims, Brief, Summary, Snapshot, Memory, Job) — these *are* the contract.
- All **routers stubbed**, returning schema-valid **mock** data. Export `openapi.json` to `packages/contracts/`.
- **DoD:** `GET /openapi.json` complete; every endpoint returns valid mock; frontend can generate its client. **Freeze the contract here.**

### B1 — Database & migrations `[Day 1]`
- SQLAlchemy models (Part 6) + initial Alembic migration. Seed script for the demo patient.
- **DoD:** `make seed` produces a patient with claims, a current-truth, a brief, a summary, and a share.

### B2 — Memory reducer `[Day 2 — highest-value backend unit]`
- `reducer.py` as a **pure, deterministic function**: `list[Claim] -> CurrentTruth`. Normalisation (drug/test/condition names), grouping, latest-wins, conflict-flagging, lab time-series, confidence-gating (Part 15).
- Unit-tested hard (this is patient-safety logic).
- **DoD:** reducer passes its unit suite; recomputes idempotently from the full claim set.

### B3 — Brief engine `[Day 2 — demo-solid core]`
- `ReasonerProvider` interface; `medgemma.py` + `mock.py`. Current Truth → **Doctor Brief JSON**. Deterministic shape; model fills content; **flags computed deterministically** (abnormal labs, missing-data, low-confidence) — not left to the model.
- **DoD:** seeded patient → real brief JSON, schema-valid, with correct flags.

### B4 — Sharing + QR `[Day 2 — demo-solid core]`
- Snapshot builder (embeds brief + current truth, frozen), `share_token`, expiry, `GET /shares/{token}` public read-only, QR generation (`qrcode`/segno).
- **DoD:** create snapshot → token → QR → fetch public snapshot. End-to-end on seeded data.

### B5 — Orchestrator + jobs `[Day 2]`
- Pipeline runner via **FastAPI BackgroundTasks** (simplest that works; *not* Celery for MVP) + **Redis job status**. Per-stage status, isolation, retry, partial-result preservation.
- **DoD:** submit a job, observe staged status transitions, retry a failed stage.

### B6 — Ingestion `[Day 2 mock → Day 3 real]`
- `POST /documents`: validate, store file (local volume; S3 optional), create `document`+`job`, enqueue pipeline.
- **DoD:** upload persists a document and starts a job.

### B7 — Extraction (provider abstraction) `[Day 3 — the risky part, isolated]`
- `ExtractorProvider` interface; `mock.py` (default), `qwen.py` (Qwen3-VL-8B), `cloud.py` (frontier fallback). Routing: try local → fallback cloud → fallback seeded. Output **Claims JSON**.
- **DoD:** a real photo → real Claims JSON; provider switchable by env; fallback chain works.

### B8 — Validation `[Day 3]`
- Pydantic schema + plausibility (dose/unit/lab ranges, date sanity, required fields) + confidence-gating → `needs_review` flags. Abstain-friendly (null > guess).
- **DoD:** malformed/implausible claims are flagged, never silently trusted.

### B9 — Summary (Marathi) `[Day 3]`
- Current Truth + Brief → **Patient Summary JSON (mr)** via MedGemma; structured template the model fills; deterministic fallback template if model output fails validation.
- **DoD:** seeded + real patient → valid Marathi summary JSON.

### B10 — Referral `[Day 3]`
- `POST /referrals`: specialty + reason (auto-derived from brief) + link to brief; optional referral snapshot.
- **DoD:** referral persists and returns confirmation.

### B11 — Demo hardening `[Day 4]`
- `DEMO_MODE`, seeded-patient fast path, cached fallbacks, model pre-warm, feature flags (Part 9 cut switches).
- **DoD:** demo path runs with network/model failures simulated.

---
# PART 5 — API contracts

Base: `/api/v1`. Auth: none for patient routes (opaque `patient_token` header `X-Patient-Token`); share routes public via `share_token`. All errors use one envelope (Part 5.7).

## 5.1 Endpoint table

| Method | Path | Purpose | Body → Returns |
|---|---|---|---|
| POST | `/patients` | Create anonymous patient | `{display_name?, lang_pref?}` → `PatientDTO` (+ token) |
| GET | `/patients/{id}` | Patient meta | → `PatientDTO` |
| POST | `/documents` | Upload doc, start pipeline | multipart `file`, `patient_id` → `{document_id, job_id, status}` |
| GET | `/documents/{id}` | Document + extraction | → `DocumentDTO` |
| GET | `/jobs/{id}` | Pipeline status (poll) | → `JobStatusDTO` |
| GET | `/patients/{id}/memory` | Current Truth + history | → `CurrentTruthDTO` |
| GET | `/patients/{id}/brief` | Latest doctor brief | → `DoctorBriefDTO` |
| POST | `/patients/{id}/brief` | (Re)generate brief | → `DoctorBriefDTO` |
| GET | `/patients/{id}/summary?lang=mr` | Patient summary | → `PatientSummaryDTO` |
| POST | `/shares` | Create share snapshot | `{patient_id, expires_in?}` → `ShareDTO` (link + QR) |
| GET | `/shares/{token}` | **Public** read-only snapshot | → `ShareSnapshotDTO` |
| POST | `/referrals` | Create specialist referral | `{patient_id, specialty, reason?}` → `ReferralDTO` |

## 5.2 Claims JSON (extraction output → validation/memory input)

```json
{
  "document_id": "doc_8f1c",
  "patient_id": "pat_2a9d",
  "extracted_at": "2026-06-20T09:31:04Z",
  "provider": "qwen3-vl-8b",
  "document_type": "prescription",
  "overall_confidence": 0.82,
  "claims": [
    {
      "claim_id": "clm_001",
      "type": "medication",
      "fields": {
        "name": "Metformin", "generic": "metformin",
        "dose": 500, "dose_unit": "mg",
        "frequency": "BD", "route": "oral",
        "duration": "30 days", "instructions": "after food"
      },
      "confidence": 0.91, "observed_at": "2026-06-18", "needs_review": false
    },
    {
      "claim_id": "clm_002",
      "type": "lab_result",
      "fields": {
        "test_name": "HbA1c", "value": 7.8, "unit": "%",
        "reference_range": "4.0-5.6", "flag": "high"
      },
      "confidence": 0.95, "observed_at": "2026-06-15", "needs_review": false
    },
    {
      "claim_id": "clm_003",
      "type": "diagnosis",
      "fields": { "condition": "Type 2 Diabetes Mellitus", "status": "active" },
      "confidence": 0.6, "observed_at": "2026-06-18", "needs_review": true
    }
  ]
}
```

**Claim `type` → required `fields`:**
- `medication`: name, dose, dose_unit, frequency *(route/duration/instructions optional)*
- `lab_result`: test_name, value, unit *(reference_range/flag optional)*
- `diagnosis`: condition, status `active|resolved|suspected`
- `allergy`: substance *(reaction/severity optional)*
- `vital`: name, value, unit
- `procedure`: name *(date optional)*
- `advice`: text

## 5.3 Doctor Brief JSON (the product)

```json
{
  "brief_id": "brf_4d2",
  "patient_id": "pat_2a9d",
  "generated_at": "2026-06-20T09:31:40Z",
  "model": "medgemma-4b",
  "one_line": "62F · T2DM, HTN · HbA1c rising · here for medication review",
  "chief_concern": "Poor glycaemic control over 3 months",
  "active_medications": [
    {"name": "Metformin", "dose": "500mg", "frequency": "BD", "since": "2026-03", "source": "doc_8f1c"}
  ],
  "recent_labs": [
    {"test": "HbA1c", "value": 7.8, "unit": "%", "flag": "high", "date": "2026-06-15", "trend": "up", "previous": 6.9}
  ],
  "active_conditions": [{"condition": "Type 2 Diabetes Mellitus", "since": "2024", "source": "doc_8f1c"}],
  "allergies": [{"substance": "Sulfa drugs", "severity": "moderate"}],
  "timeline": [{"date": "2026-06-15", "event": "HbA1c 7.8% (up from 6.9%)"}],
  "flags": [
    {"severity": "warning", "text": "HbA1c trending up despite therapy", "type": "abnormal_lab"},
    {"severity": "info", "text": "Diagnosis claim low-confidence — confirm", "type": "needs_review"}
  ],
  "suggested_questions": ["Adherence to Metformin?", "Any GI side effects?", "Diet/lifestyle changes?"],
  "source_documents": ["doc_8f1c"],
  "confidence_notes": "1 of 3 source claims flagged for review."
}
```

**`flags` are computed deterministically** by the brief engine (abnormal labs from reference ranges, `needs_review` from validation, missing-data) — the model writes prose, code decides safety flags.

## 5.4 Patient Summary JSON (Marathi)

```json
{
  "summary_id": "sum_7b1",
  "patient_id": "pat_2a9d",
  "language": "mr",
  "generated_at": "2026-06-20T09:31:55Z",
  "model": "medgemma-4b",
  "greeting": "नमस्कार, तुमच्या रिपोर्टचा सोपा सारांश:",
  "what_we_found": ["तुमची साखर (HbA1c) थोडी वाढली आहे."],
  "your_medicines": [
    {"name": "Metformin 500mg", "how_to_take": "जेवणानंतर दिवसातून दोन वेळा", "plain": "साखर नियंत्रणासाठी"}
  ],
  "what_to_watch": ["खूप थकवा, जास्त तहान किंवा चक्कर आल्यास डॉक्टरांना सांगा."],
  "next_steps": ["डॉक्टरांना भेटा आणि औषध नियमित घ्या."],
  "disclaimer": "हा सारांश माहितीसाठी आहे, वैद्यकीय सल्ल्याचा पर्याय नाही."
}
```

If model output fails schema validation → fall back to a **deterministic template** filled from Current Truth (never ship an empty/garbled summary).

## 5.5 Share Snapshot JSON (frozen, public read-only)

```json
{
  "share_id": "shr_9c0",
  "token": "k7Qm2x8Lp4",
  "created_at": "2026-06-20T09:32:10Z",
  "expires_at": "2026-06-27T09:32:10Z",
  "read_only": true,
  "patient_ref": "Patient (62F)",
  "brief": { "...": "full Doctor Brief JSON embedded at snapshot time" },
  "current_truth": { "...": "Current Truth embedded at snapshot time" }
}
```

Snapshot is **immutable** — it embeds copies, so later document uploads don't change an already-shared link.

## 5.6 JobStatus DTO

```json
{
  "job_id": "job_3e",
  "status": "running",
  "stage": "brief",
  "stages": ["extraction","validation","memory","brief","summary","share"],
  "completed_stages": ["extraction","validation","memory"],
  "progress": 0.6,
  "failed_at": null,
  "error": null,
  "document_id": "doc_8f1c",
  "result": {"brief_id": null}
}
```

## 5.7 Error envelope (all endpoints)

```json
{ "error": { "code": "EXTRACTION_FAILED", "message": "Could not read document", "details": {"stage":"extraction"}, "retryable": true } }
```

Codes: `VALIDATION_ERROR`, `EXTRACTION_FAILED`, `REASONING_FAILED`, `NOT_FOUND`, `RATE_LIMITED`, `INTERNAL`. `retryable` drives the frontend retry button.

---

# PART 6 — Database schema

PostgreSQL. UUIDs (string ids shown for readability). Timestamps UTC. **Claims are append-only; Current Truth is derived.**

```sql
-- Identity (minimal, no auth)
patients (
  id              text PK,
  display_name    text NULL,
  lang_pref       text DEFAULT 'mr',
  patient_token   text UNIQUE NOT NULL,   -- opaque, client-held
  created_at      timestamptz DEFAULT now()
)

documents (
  id              text PK,
  patient_id      text FK -> patients(id),
  doc_type        text,                   -- prescription|lab_report|discharge_summary|other
  storage_path    text NOT NULL,
  mime            text,
  source          text DEFAULT 'upload',
  status          text DEFAULT 'pending', -- pending|extracted|failed
  uploaded_at     timestamptz DEFAULT now()
)

extractions (                              -- raw provider output, audit trail
  id              text PK,
  document_id     text FK -> documents(id),
  provider        text,                    -- qwen3-vl-8b|cloud|mock
  raw_json        jsonb NOT NULL,          -- full Claims JSON as returned
  overall_confidence  numeric,
  created_at      timestamptz DEFAULT now()
)

claims (                                   -- APPEND-ONLY atomic assertions
  id              text PK,
  patient_id      text FK -> patients(id),
  document_id     text FK -> documents(id),
  claim_type      text NOT NULL,           -- medication|lab_result|diagnosis|allergy|vital|procedure|advice
  normalized_key  text NOT NULL,           -- e.g. 'metformin', 'hba1c'  (reducer grouping key)
  fields          jsonb NOT NULL,          -- type-specific payload
  confidence      numeric NOT NULL,
  observed_at     date NULL,
  needs_review    boolean DEFAULT false,
  created_at      timestamptz DEFAULT now()
  -- index: (patient_id, claim_type, normalized_key, observed_at)
)

current_truth (                            -- DERIVED snapshot (recomputed by reducer)
  id              text PK,
  patient_id      text FK -> patients(id),
  entry_type      text NOT NULL,           -- medication|lab_result|diagnosis|allergy
  normalized_key  text NOT NULL,
  value           jsonb NOT NULL,          -- resolved current value (+ history for labs)
  confidence      numeric,
  state           text DEFAULT 'confirmed',-- confirmed|needs_review|conflict|possibly_discontinued
  source_claim_ids jsonb,                  -- provenance
  updated_at      timestamptz DEFAULT now(),
  UNIQUE(patient_id, entry_type, normalized_key)
)

briefs (
  id              text PK,
  patient_id      text FK -> patients(id),
  brief_json      jsonb NOT NULL,          -- full Doctor Brief JSON
  model           text,
  generated_at    timestamptz DEFAULT now()
)

summaries (
  id              text PK,
  patient_id      text FK -> patients(id),
  lang            text DEFAULT 'mr',
  summary_json    jsonb NOT NULL,
  model           text,
  generated_at    timestamptz DEFAULT now()
)

shares (
  id              text PK,
  patient_id      text FK -> patients(id),
  token           text UNIQUE NOT NULL,    -- unguessable public token
  snapshot_json   jsonb NOT NULL,          -- frozen brief + current_truth
  view_count      int DEFAULT 0,
  created_at      timestamptz DEFAULT now(),
  expires_at      timestamptz
)

referrals (
  id              text PK,
  patient_id      text FK -> patients(id),
  brief_id        text FK -> briefs(id) NULL,
  specialty       text NOT NULL,
  reason          text,
  snapshot_json   jsonb NULL,
  created_at      timestamptz DEFAULT now()
)

-- Job status lives in REDIS (key: job:{id}), not Postgres — ephemeral, fast polling.
```

## 6.1 Memory reducer rules (Part 15) — `reducer.py`, pure & deterministic

**Input:** all `claims` for a patient. **Output:** `current_truth` rows. Recomputed in full on each new document (idempotent, replayable — simpler and safer than incremental updates).

1. **Group** claims by `(claim_type, normalized_key)`. Normalisation maps `Metformin/metformin/METFORMIN → metformin`, `HbA1c/Hb A1C → hba1c`.
2. **State-like types** (medication, diagnosis, allergy): **latest `observed_at` wins**; ties broken by **higher confidence**; if a newer document for the same patient omits a previously-active medication, mark `possibly_discontinued` (do **not** delete — conservative for safety).
3. **Time-series types** (lab_result): **keep all** as history; current value = latest; compute `trend` vs previous (`up|down|stable`). Never collapse history.
4. **Conflict**: same key, same `observed_at`, materially different value, both above threshold → `state = conflict`, surface both values, never auto-pick.
5. **Confidence gate**: any resolved entry below `CONFIDENCE_THRESHOLD` → `state = needs_review` (shown, but never presented as confirmed fact).
6. **Provenance**: every entry records `source_claim_ids`. The brief and summary read **only** from `current_truth`, never raw claims.

---
# PART 7 — Integration milestones & parallel workstreams

## 7.1 The dependency rule that enables parallelism

> **Backend cannot finalise any feature until the contract (B0) exists. Once B0 is frozen, frontend mocks everything and never blocks.**

| Need | Hard dependency | Parallel unblock |
|---|---|---|
| Frontend (all) | B0 contract / `openapi.json` | After B0: FE works fully on MSW mocks, independent of BE |
| Brief (B3) | Memory reducer (B2) | B2/B3 built on **seeded claims** — no wait for extraction |
| Share (B4) | Brief (B3) | Built on seeded brief |
| Real claims (B7) | Extraction provider | Isolated behind interface; mock provider keeps pipeline green |
| Summary (B9) | Brief (B6) | Seeded brief unblocks it |
| Referral (B10) | Brief (B6) | Seeded brief unblocks it |

**Two workstreams run truly in parallel:**
- **WS-Backend (Claude Code):** B0 → B1 → [B2,B3,B4,B5] core-on-seed → [B6/B7,B8,B9,B10] real AI → B11 hardening.
- **WS-Frontend (Claude Design):** F1 → [F2,F3,F6] core views on mocks → [F4,F5,F7] → polish + demo mode.

They meet at integration milestones, swapping mocks for real endpoints one resource at a time.

## 7.2 Integration milestones (gates — do not proceed until green)

| Milestone | When | Gate criteria |
|---|---|---|
| **M1 — Contract frozen** | End Day 1 | `openapi.json` complete; FE generates client + renders all screens on mocks; BE returns schema-valid mocks; FE↔BE smoke (one real call). |
| **M2 — Demo-solid core** | End Day 2 | Seeded patient → **real reducer → real brief → real share/QR** end-to-end; FE renders real brief + scannable QR. **This is the product. Freeze & protect it.** |
| **M3 — Real pipeline** | End Day 3 | Real photo → extraction → claims → memory → brief → **Marathi summary** → share; referral works; fallback chain verified. |
| **M4 — Demo-ready** | End Day 4 | Demo mode + fallbacks + pre-warm; rehearsed twice; <90s; no console errors; DoD (Part 10) all checked. |

---

# PART 8 — 4-day implementation plan

### Day 1 — Foundations & contract freeze → **M1**
- **BE:** monorepo, docker-compose (db/redis/api/web), `config.py`, **all DTOs**, **all routers stubbed with valid mocks**, export `openapi.json`. DB models + first Alembic migration + seed script started.
- **FE:** Next.js PWA shell, Tailwind/shadcn, **generate typed client**, MSW handlers for every endpoint, render Home/Upload/Brief/Memory/Share on mocks.
- **Gate M1:** contract frozen; FE on mocks; one real FE→BE call works.

### Day 2 — Demo-solid core on seeded claims → **M2** (most important day)
- **BE:** **reducer (B2) + unit tests**, **brief engine (B3, MedGemma)**, **share+QR (B4)**, orchestrator+jobs (B5). All on seeded claims.
- **FE:** real upload→job-polling (against B5), polished Brief view (F3), Share/QR view + public snapshot page (F6), memory timeline shell (F5).
- **Gate M2:** seeded patient → real brief → scannable QR, end-to-end. **Protect this build (tag it).**

### Day 3 — Real extraction, summary, referral → **M3**
- **BE:** extraction provider abstraction + Qwen3-VL-8B + cloud fallback (B7), validation (B8), Marathi summary (B9), referral (B10), real ingestion (B6).
- **FE:** wire real upload→extraction→brief, Marathi summary view (F4), memory timeline real data (F5), referral flow (F7), all error/empty states.
- **Gate M3:** real photo → full pipeline → brief+summary+share; referral works.

### Day 4 — Harden, fallback, rehearse → **M4**
- **BE:** demo mode, seeded fast-path, cached fallbacks, model pre-warm, feature-flag cut switches (B11).
- **FE:** demo polish, performance, offline/poll resilience, final pass.
- **Both:** bug bash, **rehearse the demo script twice**, verify <90s, freeze.
- **Gate M4:** Definition of Done (Part 10) fully checked.

**Slip policy:** if Day 3 slips, the M2 seeded core still demos the product. If Day 4 slips, cut from the Part-9 cut list — never cut from the M2 core.

---

# PART 9 — Risk register

| # | Risk | Likelihood | Impact | Mitigation | Cut/fallback |
|---|---|---|---|---|---|
| R1 | Handwriting extraction inaccurate | High | High | Confidence-gating + validation; demo with clean/printed docs; cloud fallback | Seeded claims path |
| R2 | Model cold-start / GPU unavailable | Med | High | Pre-warm at startup; mock+cloud providers; cached demo results | `DEMO_MODE` seeded patient |
| R3 | >90s latency | Med | Med | Parallelise summary+share after brief; pre-warm; staged progress UI | Show brief first, summary lazy |
| R4 | FE/BE contract drift | Med | High | Contract-first; CI openapi-drift check; one resource swapped at a time | MSW mocks stay as fallback |
| R5 | Reducer bug corrupts memory | Med | High | Pure function + hard unit tests; idempotent recompute; provenance | Recompute from claims |
| R6 | Marathi summary garbled | Med | Med | Structured template model fills; schema-validate output | Deterministic template fallback |
| R7 | Scope creep | High | High | DoD locked; this cut list | see below |
| R8 | Demo network failure | Med | High | Fully local demo mode; cached snapshots; QR served locally | Offline seeded demo |

**Cut list (in order, if time-pressured) — never touch the M2 core:**
1. Referral flow (F7/B10) → 2. Marathi summary live-gen (B9) → use pre-generated → 3. Real extraction (B7) → demo on seeded/cloud only → 4. Memory history sparklines → latest-only. **Brief + Memory + QR share are never cut.**

## 9.1 Git, env, docker, dev workflow

**Git (trunk-based, simplest for 4 days/2 agents):** `main` always demo-able & protected (CI must pass). Short-lived branches `be/<feature>`, `fe/<feature>` → PR → squash-merge. Merge frequently (≥ daily) to avoid integration debt. **Tag `demo-m2` and `demo-final`.** No `develop`, no gitflow.

**Environment variables (`.env.example`):**
```
# API
DATABASE_URL=postgresql+psycopg://setu:setu@db:5432/setu
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=dev-only
LOG_LEVEL=info
MAX_UPLOAD_MB=15
CONFIDENCE_THRESHOLD=0.7
STORAGE_PATH=/data/uploads
SHARE_BASE_URL=http://localhost:3000/share
# AI providers (abstraction)
EXTRACTION_PROVIDER=mock          # mock|qwen|cloud
QWEN_ENDPOINT=http://models:8001/v1
CLOUD_VLM_PROVIDER=               # claude|openai|mistral
CLOUD_VLM_API_KEY=
REASONING_PROVIDER=mock           # mock|medgemma
MEDGEMMA_ENDPOINT=http://models:8002/v1
# Demo
DEMO_MODE=false
SEED_PATIENT_ID=pat_demo
# Web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEMO_MODE=false
```

**Docker:** `infra/docker-compose.yml` runs `db`, `redis`, `api`, `web`. **Default providers are `mock`, so the whole stack runs with zero GPU.** Models run separately (GPU box) via `docker-compose.models.yml` (vLLM Qwen3-VL on :8001, MedGemma on :8002) and are referenced by env endpoints. This keeps every developer (and CI) unblocked without a GPU.

**Local dev workflow:**
```
make dev         # docker-compose up (db, redis, api hot-reload, web hot-reload) — mock providers
make seed        # load demo patient (claims + brief + summary + share)
make gen-client  # export openapi.json -> generate web/lib/api-client
make test        # backend pytest (reducer, pipeline smoke) + web tests
```
Switch to real AI by setting `EXTRACTION_PROVIDER=qwen` / `REASONING_PROVIDER=medgemma` and pointing endpoints at the model box.

---

# PART 10 — Definition of Done (June 20 demo)

A checkbox gate. The demo is "done" only when **all** are true.

**Demo-solid core (must, 100% reliable):**
- [ ] Seeded patient loads instantly via `DEMO_MODE` (no network/model dependency).
- [ ] Current Truth (memory) renders: meds, latest labs + trend, conditions, allergies, provenance.
- [ ] Doctor Brief renders complete: one-liner, meds, labs+flags, conditions, allergies, timeline, suggested questions; low-confidence/flagged items visually distinct.
- [ ] Share → **QR scannable on a second device** → public read-only snapshot loads fast.
- [ ] Reducer unit tests pass; memory is provenance-traceable.

**Real pipeline (must work on curated demo docs):**
- [ ] Upload a real (printed) document → full pipeline → brief in **< 90s**, staged progress shown.
- [ ] Extraction falls back (qwen → cloud → seeded) without crashing if a provider fails.
- [ ] Marathi summary renders correctly (Devanagari intact, plain language).
- [ ] Validation flags implausible/low-confidence fields; nothing unsafe shown as confirmed fact.

**Quality & resilience (must):**
- [ ] Every screen has loading/empty/error states; failed stages are retryable.
- [ ] No uncaught console errors; PWA installs; mobile layout clean.
- [ ] App runs end-to-end with `EXTRACTION_PROVIDER=mock` (no GPU) — proves demo independence.
- [ ] `main` builds green in CI; `demo-final` tagged.
- [ ] **Demo script rehearsed twice**, end-to-end, on the actual demo device/network.

**Explicitly NOT required for June 20 (Phase 2):** doctor accounts, video, AI triage, ABDM, real-time multi-user, multi-language beyond mr/en, fine-tuned models.

---

# PART 11 — Testing strategy

Prioritised for a 4-day window — test the things whose failure is **silent and dangerous**, skip the rest.

1. **Reducer unit tests (highest priority).** Pure function → easy + critical. Cover: latest-wins, confidence tie-break, lab time-series/trend, conflict flagging, possibly-discontinued, confidence gate. Memory correctness = patient safety.
2. **Validation unit tests.** Plausibility ranges, required fields, abstain handling.
3. **Contract test.** CI checks committed `openapi.json` matches live FastAPI schema (no drift).
4. **Pipeline integration smoke.** With `mock` providers: document → claims → truth → brief → summary → share, asserting schema-valid output at each stage.
5. **One E2E happy path.** Seeded patient → brief → QR → public snapshot. Run before every demo rehearsal.
6. **Frontend.** Light: render Brief/Summary/Memory from fixture JSON; upload→poll flow against MSW. No exhaustive coverage — it's a hackathon.

**Not doing:** load testing, security pen-testing, exhaustive E2E matrices, model accuracy benchmarking (that's the separate eval harness, not demo-blocking).

---

*Plan optimised for speed, demo reliability, developer productivity, low integration risk, and zero scope creep. When in doubt: simpler implementation, protect the M2 core, cut from the Part-9 list.*
