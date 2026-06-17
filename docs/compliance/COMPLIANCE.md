# SETU Compliance Checklist (DPDP + HIPAA-equivalent)

Dual-track compliance posture for production deployment. This is an internal engineering checklist — not legal certification.

## India DPDP (Digital Personal Data Protection Act)

- [x] Explicit consent before document processing (`consent.py`, onboarding flow)
- [x] Consent withdrawal without blocking account deletion path
- [x] Data principal access log (`GET /patients/{id}/access-log`)
- [x] Erasure / retention purge for uploaded images (`retention.py`)
- [x] Purpose limitation documented in patient privacy UI (`/settings`)
- [ ] Publish privacy notice URL on production domain (ops)
- [ ] Appoint DPO contact in privacy notice (ops)

## HIPAA-equivalent technical controls

- [x] Encryption at rest for uploads (local AES / S3 SSE via `storage.py`)
- [x] TLS in transit (HTTPS API + Vercel CDN)
- [x] Role-based access control (Supabase JWT + `deps.py`)
- [x] Universal PHI read audit (`audit_phi.py` on brief, memory, documents, timeline, provider brief)
- [x] Provider verification workflow before clinical access (`verification_status`)
- [x] Authenticated provider patient access grants (`provider_access_grants`)
- [ ] BAA with cloud vendors (Supabase, Vercel, Gemini, SMS provider) — legal
- [ ] Annual access review process — ops

## Operational security

- [x] Production env validation (`PRODUCTION=true` gate in `config.py`)
- [x] Secrets outside repo (`.env.example` only)
- [x] CI: ruff + pytest on PR (`.github/workflows/ci.yml`)
- [x] Error tracking hook (Sentry DSN in `main.py` lifespan)
- [ ] Database PITR enabled on Supabase project — ops
- [ ] On-call runbook — ops (`infra/DEPLOY.md` + this doc)

## Breach response (runbook outline)

1. Contain: revoke compromised tokens, rotate `SECRET_KEY` and service keys
2. Assess: query `access_logs` for affected `patient_id` range
3. Notify: data principals per DPDP timelines; legal review for HIPAA-covered flows
4. Remediate: patch vulnerability, re-run deploy checklist

## Data flows requiring audit

| Resource | Audited |
|----------|---------|
| Brief | Yes |
| Memory / current truth | Yes |
| Document list | Yes |
| Patient timeline | Yes |
| Provider patient brief | Yes |
| Share token (public) | Share view logged |

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering lead | | |
| Security / compliance | | |
