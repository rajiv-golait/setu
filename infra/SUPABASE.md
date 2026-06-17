# Supabase setup (product auth + hosted Postgres)

SETU uses Supabase for **phone OTP auth** and **hosted Postgres**. FastAPI remains the only writer to PHI tables.

## 1. Create project

1. Go to [supabase.com](https://supabase.com) → New project.
2. Pick a region close to your users (note data-residency for pitch).
3. Save the database password.

## 2. Enable phone auth

1. **Authentication → Providers → Phone** → Enable.
2. Configure SMS: **Twilio** or **MessageBird** (required for real OTP in India).
3. Test with one Indian mobile number before demo day.

## 3. Copy credentials to `.env`

From **Project Settings → API**:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ENABLED=true

NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_SUPABASE_ENABLED=true
```

## 4. Create SETU tables in Supabase

Your project ref: **sevwzahlsunwqbiowbcx** (`https://sevwzahlsunwqbiowbcx.supabase.co`).

### Option A — SQL Editor (easiest, no local Alembic)

1. **SQL Editor → New query**
2. Paste the contents of [`supabase-schema.sql`](./supabase-schema.sql) (or `supabase-migrations.sql` — same clean SQL; **not** raw `alembic --sql` output)
3. **Run** — creates all tables + `alembic_version` at `0006`
4. (Optional) Run [`supabase-rls.sql`](./supabase-rls.sql) to block direct anon access

### Option B — Alembic from your machine

```powershell
# From repo root (Windows)
$env:SUPABASE_DB_PASSWORD = "your-database-password"
.\infra\scripts\migrate-supabase.ps1
```

Uses the **direct** connection (`db.<ref>.supabase.co:5432`) for DDL.

### Option C — Docker

```bash
# Set DATABASE_URL in .env to the direct URI first, then:
cd infra && docker compose run --rm -e DATABASE_URL api alembic upgrade head
```

## 5. Point DATABASE_URL at Supabase (runtime)

**Local dev** — use the **pooler session** URI from your dashboard (port **5432**).
Do not guess the region: run `python scripts/find_pooler.py` from `apps/api`, or copy the host from **Dashboard -> Database -> Connection string**.

Example for this project (`sevwzahlsunwqbiowbcx`):

```env
DATABASE_URL=postgresql+psycopg://postgres.sevwzahlsunwqbiowbcx:[password]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require
SUPABASE_DB_PASSWORD=your-database-password
```

**Note:** `db.<ref>.supabase.co` is often IPv6-only; Windows without IPv6 may fail DNS. Use the pooler host instead.

Set `SUPABASE_DB_PASSWORD` in **`apps/api/.env`** (loaded after repo-root `.env`).

## 6. Security notes

- **RLS:** Enable on PHI tables; deny direct anon/authenticated access. The API uses the service connection string only.
- **Never** expose `SUPABASE_SERVICE_ROLE_KEY` in the web app — only `ANON_KEY` in `NEXT_PUBLIC_*`.
- Public brief/share routes (`/brief/{token}`) stay unauthenticated by design.

## 7. Local dev without SMS

Keep legacy anonymous mode:

```env
SUPABASE_ENABLED=false
NEXT_PUBLIC_SUPABASE_ENABLED=false
```

The web app skips login; `POST /patients` creates anonymous records.

## 8. Admin: register doctors

1. Set **`SUPABASE_SERVICE_ROLE_KEY`** in `apps/api/.env` (Dashboard → Project Settings → API → `service_role` secret — **never** expose in the web app).
2. Grant yourself admin once in Supabase → Authentication → Users → Raw App Meta Data: `{"role": "admin"}`.
3. Sign in as admin → **`/admin/doctors`** → enter mobile, name, specialty → **Grant doctor access**.
4. Doctor signs in at **`/doctor/login`** with that number.

Revoke sets the Supabase role back to `patient` and removes the provider row.

## 9. Verify auth E2E

1. Open web → `/login` → enter phone → OTP.
2. Complete `/onboarding` (language).
3. Grant consent on home → upload → `/summary` → brief → share on second device.

See [DEPLOY.md](./DEPLOY.md) for public URL wiring.
