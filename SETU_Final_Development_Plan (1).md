# SETU — Final Development Plan

**Status:** LOCKED. This supersedes the Frozen Product Spec and consolidates every decision made through the planning phase — product, architecture, AI/model choices, voice, hosting, pitch narrative, and the 4-day build. This is the single source of truth the whole team builds from. Do not reopen settled decisions.

**Dates:** Build Jun 14–17 · Submit Jun 17 · Demo Jun 20.
**Team:** 1 backend dev (Claude Code) · 1 frontend (Frontend Claude) · 6 humans (documents, benchmarking, Marathi validation, real-user testing, pitch, rehearsal).

---

## 0. Decision log (locked — these are closed)

| # | Decision | Rationale |
|---|---|---|
| D1 | **Product = WhatsApp document-explainer + doctor brief**, not a telehealth/records app | Survives the stakeholder simulation; routes around every dead user behavior |
| D2 | **Primary user = the caregiver**, patient is beneficiary | Sim proved the patient won't operate an app; the caregiver is the real health manager |
| D3 | **Channel = Telegram** (Bot API for demo/build), web-chat fallback; **WhatsApp = Phase 2** | Telegram ships in minutes (no Meta/Twilio approval) → lowest 4-day integration risk; WhatsApp is the production channel where the ICP actually is |
| D4 | **Lead value = understanding in your language**, memory is a byproduct | Nobody felt "continuity/memory" pain; everybody feels "is this report bad?" |
| D5 | **AI for demo = cloud** (provider-abstracted); **local later** | One dev, 4 days, demo reliability; local handwriting isn't safely solved today |
| D6 | **Phase-2 local extractor = `parrotlet-v-lite-4b` on Lightning.ai** | MIT-licensed, Indian-medical purpose-built, MedGemma-family; removes API lock-in |
| D7 | **Voice = deferred to Phase 2**; if added, **Sarvam default / Whisper fallback** | Voice serves the de-prioritized patient-direct path; Sarvam wins on Indic medical speech |
| D8 | **Doctor = glance-only**, no scan/login/app | Both simulated doctors refuse to engage with an interface |
| D9 | **Beachhead = Type 2 Diabetes**, Tier 1–2 cities | HbA1c gives a provable adherence marker; richest document corpus |
| D10 | **KILLED: AI auto-triage and AI diet/lifestyle advice** | Medical-device + medical-advice territory; regulatory/liability risk |
| D11 | **Pitch = "Healthcare Bridge" vision; demo = the wedge** | Bridge narrative scores against the PS; the demo stays honest, safe, buildable |
| D12 | **Reducer (Claims→Truth) stays pure-Python and ours** | The one real differentiator + the safety core; never outsourced |

---

## 1. Product definition

**SETU is a chat-based health assistant (Telegram for the build/demo, WhatsApp in production): a caregiver forwards a photo of any prescription or lab report, and SETU replies in their own language (Marathi/Hindi/English) explaining what it says and whether anything needs attention — while silently assembling a one-page, doctor-ready summary they can pull up at the next visit.** No app to install, no forms, no organizing papers. The patient never operates anything. The caregiver does one thing they already do daily — forward a photo in a chat app — and gets understanding now plus a clean brief later. (Telegram is the demo/prototype channel for build speed; WhatsApp is the production channel where this daily behavior actually lives — a drop-in adapter behind the same backend.)

- **Primary user:** the caregiver (adult child / spouse).
- **Secondary:** the patient (beneficiary) and the doctor (passive glance).
- **JTBD:** *"When my parent or I get a confusing medical document, help me understand it and know if I should act — and have it ready for the doctor."*
- **The one reason to return:** *"Every new report or prescription, SETU instantly tells me what it means and whether to worry — in my language."*

---

## 2. Scope freeze

### P0 — the demo is exactly these seven things
1. **Forward-a-document intake** (Telegram Bot API; web-chat mirrors it; WhatsApp adapter is Phase 2).
2. **Cloud extraction → structured claims** (prescription: drug/dose/frequency; lab: test/value/range/flag) as validated JSON.
3. **Deterministic reducer → current truth** (reconciled meds + latest labs with flags).
4. **Plain-language explanation reply** in Marathi/Hindi/English — never a dose change.
5. **One-page doctor brief at a shareable link** (no doctor login, no QR dependency).
6. **Confidence + safety guardrails** on every output (low-confidence flagged "verify with original"; "not medical advice"; abstain on unreadable).
7. **Demo fallback mode** (fully cached patient, zero live dependency).

### P1 — only if all P0 is done
Longitudinal trend view (HbA1c across visits) · follow-up reminder (logistics only) · caregiver-remote ping + view · both Marathi and Hindi validated.

### P2 — rejected for the hackathon
Video/teleconsult · doctor accounts/dashboards · pharmacy/pharma integration · ABDM/DigiLocker auto-pull · local AI serving in the 4-day window · payments · Indic model fine-tuning · multi-condition breadth beyond diabetes · voice.

### KILLED outright (do not build, do not pitch as built — regulatory)
- **AI auto-triage / "Critical/Priority/Routine" categorization.** Acuity triage from symptoms is clinical decision-making → CDSCO medical-device territory; a false "Routine" on a cardiac event is fatal + a lawsuit.
- **AI diet/lifestyle "recommendations."** Crosses from explaining documents into medical advice without a doctor → Telemedicine Guidelines violation.
SETU explains what a document says and says "discuss with your doctor." It never tells anyone what to do.

---

## 3. Final architecture

One channel-agnostic FastAPI backend. Cloud AI for the demo, abstracted so local drops in later. No option trees.

```
 Caregiver (WhatsApp)                                  Doctor (glance only)
   │ forwards photo/PDF                                      ▲ shown on phone / sent link
   ▼                                                         │
 ┌──────────────┐    ┌────────────────────────────────────────────────────────┐
 │ Telegram Bot │    │                  SETU BACKEND (FastAPI, async)           │
 │ (demo/build) │───▶│  /inbound ─▶ Orchestrator (BackgroundTasks + Redis)       │
 │ + web-chat   │    │   (channel-agnostic; WhatsApp adapter = Phase 2)          │
 │   fallback   │    │  Ingestion ─▶ ExtractorProvider ─▶ Validation ─▶ Reducer │
 └──────────────┘    │   (store)      │  cloud (demo)      (plausibility   (pure │
                     │                │  parrotlet (P2)     +confidence)    Py)  │
                     │                └──▲ provider abstraction ─────────┐  │     │
                     │   ReasonerProvider (cloud): Marathi explanation + │  │     │
                     │   doctor-brief JSON ◀─────────── current truth ───┘  │     │
                     │   TranscriberProvider (P2): Sarvam / Whisper          │     │
                     │                                                       ▼     │
                     │   Postgres (patients, documents, claims, current_truth,    │
                     │   briefs) · Redis (status/cache) · S3/disk (raw docs)      │
                     │   Next.js: /brief/{token} (public) + web-chat fallback     │
                     └────────────────────────────────────────────────────────────┘
```

**Locked choices:**
- **Frontend:** minimal **Next.js** (Tailwind + shadcn/ui) — the public **doctor brief page** + the **web-chat fallback**. No heavy PWA features.
- **Backend:** **FastAPI** single async service (modular internally). **BackgroundTasks + Redis** for the pipeline/status — not Celery.
- **Storage:** **PostgreSQL** + SQLAlchemy + Alembic; **Redis**; **S3/local volume** for raw images.
- **Reducer:** deterministic **claims → current truth** in pure Python — latest-observed wins, conflicts flagged, labs as time-series with trend, low-confidence `needs_review`, idempotent recompute. **This is ours and stays ours.**
- **Sharing:** tokenized **web link** to an immutable brief snapshot. QR optional convenience only; demo never depends on a doctor scanning.
- **Deploy:** Docker Compose on a single cloud VM for the demo.
- **ABDM/DigiLocker:** none in MVP — designed as a future Ingestion adapter behind the same interface.

---

## 4. AI stack (final)

**Demo (Jun 20): CLOUD, behind a provider abstraction.** One frontier vision-language model does OCR + layout + structured extraction in a single call → JSON with per-field confidence. Same/similar cloud model generates the Marathi explanation and the doctor-brief JSON. Chosen for demo reliability and because handwritten Marathi-English extraction is not safely solvable on local/student hardware today.

**Three provider interfaces (so nothing is locked):**
- `ExtractorProvider` — **cloud now → `ekacare/parrotlet-v-lite-4b` later.**
- `ReasonerProvider` — cloud now (explanation + brief).
- `TranscriberProvider` — unused in MVP; **Sarvam default / Whisper fallback** when voice ships.

**Safety rules (enforced in code AND prompt — non-negotiable):**
1. Never suggest starting/stopping/changing a dose. Explain + "discuss with your doctor."
2. Every output: *"This is an explanation of your document, not medical advice."*
3. Per-field confidence shown; low-confidence fields flagged "verify against the original."
4. Reasoning layer may only describe **validated, extracted** claims — cannot introduce facts not in the document.
5. **Abstain over guess:** unreadable/low-confidence → "please re-send a sharper photo or check with your doctor," never a fabricated value.
6. Doctor brief shows **source document + confidence per line** — trust-but-verify at a glance.

**Phase-2 local path (decided, deferred):**
- **Model:** `ekacare/parrotlet-v-lite-4b` — MIT license, purpose-built for Indian lab reports + prescriptions, built on MedGemma-4b (the family already in our stack). Slots into `ExtractorProvider` with zero downstream change.
- **Hosting:** **Lightning.ai** GPU endpoint. Removes proprietary-API lock-in and gives data residency. *Honest framing:* this trades cloud-API dependency for cloud-GPU + open-weights dependency — predictable and un-revocable (MIT), but say "no proprietary lock-in + India residency," not "no dependencies."
- **Caveat:** parrotlet is tuned for *digital/printed* docs; it does **not** retire the handwriting risk, and has no published benchmarks we've verified. **Benchmark it on our 50 real docs (Day 2) before trusting it.** Use Lightning for dev/benchmark first, persistent serving post-hackathon.
- **Note:** it's a competitor's (Eka's) model — fine at the commodity extraction layer (extraction was never the moat), but never near the reducer.

---
## 5. User flows (the ones that ship)

- **First-time (caregiver):** start the Telegram bot (`/start`) → pick language once → "Forward a photo of any prescription or lab report." `patient_created`.
- **First document:** forward photo → "Reading your report…" → plain-language explanation + any low-confidence note. `ingested → extracted → validated → explained → truth_updated`.
- **Returning:** forward any new document any time → updated explanation + "this updates your summary"; reducer recomputes, trend updated for repeat labs.
- **Get the brief:** send "summary" → tokenized brief link.
- **Doctor interaction (passive):** caregiver shows the brief on their phone or sends the link beforehand; doctor glances ~10s; no login/scan/app. Read-only snapshot.
- **Caregiver-remote [P1]:** ping when a new document is added; open the brief from anywhere (solves "managing a parent from another city").
- **Specialist/remote consult:** caregiver sends the brief link ahead of a consult that happens on someone else's platform. SETU supplies context; it does **not** host the call.

---

## 6. 4-Day build plan (with team split)

### Day 1 (Jun 14) — Backbone + contract
- **Claude Code:** FastAPI skeleton; Postgres models (patients, documents, claims, current_truth, briefs) + Alembic; Redis; the three provider interfaces with **mock** implementations; `/inbound` + `/brief/{token}` stubs returning seed data; Docker Compose; **seed patient "Ramesh."**
- **Frontend Claude:** Next.js app; doctor-brief page + web-chat fallback UI on mocks.
- **Team:** collect **50 real documents** (handwritten Rx, lab reports, discharge summaries, Marathi-mixed, phone photos); create the **Telegram bot** (BotFather) + token.
- **Gate:** end-to-end on mocks; brief link renders; web-chat talks to backend.

### Day 2 (Jun 15) — Real AI + reducer (the core day)
- **Claude Code:** wire **cloud extraction** (real) → validation → **deterministic reducer** (real, unit-tested) → persist claims/current_truth; real **Marathi explanation**; confidence + safety guardrails.
- **Frontend Claude:** brief page polished — source+confidence badges, lab trend, loading/empty/error states.
- **Team:** **extraction benchmarking** — run the 50 real docs through (a) the cloud extractor and (b) **`parrotlet-v-lite-4b` on Lightning.ai**, hand-score drug/dose/lab accuracy, log failure cases; begin **Marathi validation** with a native speaker.
- **Gate:** forward a real printed document → real explanation + real brief, end-to-end. (Benchmark data tells us if/when to switch to parrotlet.)

### Day 3 (Jun 16) — WhatsApp hero + P1 + harden
- **Claude Code:** wire **Telegram Bot API** end-to-end (hero path: receive photo → reply explanation); P1 if time (follow-up flag, caregiver ping); build the **cached demo patient** + pre-warm.
- **Frontend Claude:** final brief polish; cached demo path in web-chat.
- **Team:** full **testing** on real + bad inputs (blurry, multi-page, wrong photo); Marathi sign-off; **draft the pitch** around the demo + bridge narrative.
- **Gate:** Telegram bot works on the demo phone; fallbacks tested by unplugging the network.

### Day 4 (Jun 17) — Freeze, rehearse, submit
- **Claude Code + Frontend:** bug-bash only. **Feature freeze.** Record the 60-second fallback video. Tag the build.
- **Team:** **rehearse the 3-min demo twice** on the actual device/network; finalize pitch; submit.
- **Gate:** demo runs clean twice; fallback video exists; submitted.

### Parallel human workstream (all 4 days — real validation, not theater)
Two members take the demo + 50 docs to **5 real diabetics, 2–3 GPs, 1 specialist.** Ask, don't pitch: does the caregiver forward a *second* time; does the Marathi explanation land; does a doctor glance >10s; what's real-handwriting extraction accuracy. **Output: the one slide judges and investors respect most — "here's what real users told us this week."**

---

## 7. Demo script (3 min — must succeed)

**Patient:** Ramesh Shinde, 58, T2D + HTN, Ahmednagar. **Operator:** son Akash (presenter). **Pre-seeded:** prior visit in memory (Metformin 500mg BD; HbA1c 8.4%, 3 months ago). Demo phone has the Telegram bot open; every step cached for fallback.

- **0:00–0:30 — Problem:** hold up the crumpled plastic bag. "This is how 100M Indian families manage chronic illness. Akash lives in Pune; this is what he works with."
- **0:30–1:30 — Magic moment (live):** Akash forwards a new lab report (HbA1c 9.1%) to the SETU bot on Telegram. ~30s later SETU replies in Marathi: *"तुमची साखर ९.१% आहे — मागच्या वेळेपेक्षा वाढली आहे. ही जास्त आहे. कृपया डॉक्टरांशी बोला."* "He understood his father's report in 30 seconds, in his mother's language, from another city."
- **1:30–2:20 — The brief:** Akash sends "summary" → link → clean one-pager: *62M, T2DM+HTN; Metformin 500mg BD; HbA1c 9.1% ↑ (was 8.4%); follow-up overdue* — source + confidence per line. "At the visit, the doctor sees this in 10 seconds instead of sorting a bag for 12 minutes."
- **2:20–3:00 — Close:** "No new app, no forms — he forwarded a photo in a chat, the thing he already does all day (WhatsApp in production; Telegram here). SETU explained it and built a doctor-ready memory as a byproduct. That's the wedge into India's chronic-care continuity gap."

**Fallbacks (the demo cannot fail):** internet/Telegram down → web-chat on same backend; extraction/AI slow → cached demo patient renders instantly; link fails → brief already open in a second tab; total failure → 60-second recorded screen-capture on the laptop. **Rule: never debug live — cut to the cached/recorded path and keep talking.**

---

## 8. Pitch narrative (vision vs. demo)

**Pitch the bridge. Demo the wedge. Label the difference honestly.**

- **Narrative (the story judges/investors hear):** *"SETU is an AI healthcare bridge — connecting patients, local doctors, and specialists through a shared, intelligent medical memory, so care is continuous instead of fragmented."* This maps cleanly to the PS (patient data ✅, multilingual accessibility ✅, specialist gets context ✅, continuity ✅).
- **Demo (what we actually show working):** the chat explainer + the doctor brief — the safe, buildable slice that is already *inside* the bridge vision. (Demoed on Telegram for reliability; framed for WhatsApp in production, where the ICP's daily forwarding behavior lives.)
- **Roadmap slide (deferred, labeled as future):** specialist routing, follow-up engine, voice (Sarvam), local AI (parrotlet on Lightning), ABDM/auto-ingestion.
- **Do NOT pitch as built or coming:** AI auto-triage and AI diet/lifestyle advice — state plainly these are deliberately excluded for patient-safety/regulatory reasons. (Turning a kill into a *credibility* point: "we deliberately don't let AI triage acuity or change doses — that's a doctor's job.")

---

## 9. Risks

### Accepted (for these 4 days)
- **Manual forwarding friction** — mitigated: forwarding a photo in a chat is an existing behavior, far lighter than app-upload. (Permanent fix = auto-ingestion, Phase 2.)
- **Imperfect extraction on worst handwriting** — mitigated: confidence flags, abstain, curated demo inputs.
- **"Understanding" hook may not retain long-term** — tested with real users in parallel, not assumed.
- **Cloud cost/dependency** — accepted at demo scale; abstracted for the parrotlet/Lightning swap.

- **Channel mismatch (Telegram ≠ where users are)** — accepted for the demo; the real friction test must run on **WhatsApp** post-hackathon, since that's the ICP's daily channel. Backend is channel-agnostic, so this is an adapter swap.

### Tested now, in parallel (these can still kill it)
1. Will a caregiver forward a document a **second** time, unprompted, after week one? *(the documented silent killer)*
2. Does a real doctor glance at the brief **>10 seconds** in a real OPD?
3. **Extraction accuracy** on 50 real handwritten/Marathi docs — safe, not just demoable?
4. Does the **Marathi explanation** feel valuable to a real patient/caregiver?

If #1 and #3 fail, accelerate the move to **auto-ingestion** (ABDM/DigiLocker/lab APIs) — the abstractions make that an adapter, not a rewrite.

---

## 10. Phase-2 roadmap (after Jun 20, decided but deferred)

1. **Local extractor:** benchmark-gated switch to `parrotlet-v-lite-4b` on Lightning.ai behind `ExtractorProvider` — only when it matches cloud on dose/drug/lab accuracy on real docs.
2. **Voice (if validated):** `TranscriberProvider` with **Sarvam default / Whisper fallback** — but first record 20–30 real Marathi-medical clips and benchmark drug/dose accuracy; voice serves the patient-direct path, so confirm it earns its place.
3. **WhatsApp production channel:** drop-in messaging adapter behind the same `/inbound` handler (Meta Business / a provider like Gupshup or Twilio) — the real channel where the caregiver's daily forwarding behavior lives. Telegram was the build/demo proxy.
4. **Auto-ingestion (the real moat):** ABDM/DigiLocker pull + lab APIs (Metropolis/SRL) so documents arrive without anyone forwarding — the permanent fix for the data-layer killer.
5. **Continuity engine:** follow-up + refill drop-off detection grounded in the reconciled memory (the chronic-care thesis), once retention is proven.
6. **Payer validation (parallel, non-eng):** the data-grounded adherence angle → pharmacy first, pharma PSP later. Prove a refill-continuity number on real patients before any B2B room.

---

## 11. Founder decision

- **Build:** the Telegram document-explainer + doctor brief (WhatsApp in production), caregiver-operated, cloud AI behind a provider abstraction, deterministic reducer, cached fallback. Beachhead: T2D.
- **Defer:** WhatsApp production adapter, parrotlet-on-Lightning local AI, Sarvam voice, auto-ingestion, the full bridge platform.
- **Kill:** AI auto-triage, AI diet/lifestyle advice (regulatory) — and use the kill as a credibility point.
- **Accept (uncertain but OK for now):** forwarding is light enough; understanding is a strong-enough wedge; cloud extraction is safe enough on typical docs.
- **Test immediately:** second-time forwarding, real-OPD doctor glance, real-handwriting accuracy, Marathi value — all in the parallel field workstream.

> **This is the product we stop debating and start building tomorrow. Ship the wedge on Telegram, pitch the bridge, plan WhatsApp for production, test the assumptions, and keep the reducer ours.**
