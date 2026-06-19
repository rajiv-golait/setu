# Deploy `apps/api` to Railway

## Live

| | URL |
|---|---|
| **API** | https://setu-api-production.up.railway.app |
| **Health** | https://setu-api-production.up.railway.app/health |
| **Dashboard** | https://railway.com/project/acd1df41-86cd-4ec1-8723-651e8094d926 |

Redis runs as a sibling service in the same project (`REDIS_URL=${{Redis.REDIS_URL}}`).
Postgres stays on **Supabase** — set `DATABASE_URL` + `SUPABASE_DB_PASSWORD` on the API service.

## Redeploy from CLI

```bash
cd apps/api
npx @railway/cli@latest login          # once
# IMPORTANT: always target setu-api — never run `railway up` without --service
# (a bare `railway up` can overwrite the Redis service with the API image).
npx @railway/cli@latest up --detach -y --service setu-api
```

If Redis shows **Completed/Exited** or uploads fail with `TimeoutError` on Redis:

```bash
npx @railway/cli@latest redeploy --service Redis --from-source -y
npx @railway/cli@latest redeploy --service setu-api -y
```

## Required env vars (Railway → setu-api → Variables)

| Var | Notes |
|-----|--------|
| `DATABASE_URL` | Supabase pooler URI (`[password]` placeholder OK) |
| `SUPABASE_DB_PASSWORD` | Substituted into `DATABASE_URL` at startup |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` when using Railway Redis |
| `SECRET_KEY` | Random hex — required when `PRODUCTION=true` |
| `PRODUCTION` | `true` |
| `SUPABASE_*` | URL, anon key, JWT secret, `SUPABASE_ENABLED=true` |
| `GOOGLE_API_KEY` | Gemini extraction/reasoning |
| `CORS_ORIGINS` | Include `https://web-iota-eight-59.vercel.app` |
| `BRIEF_BASE_URL` | `https://web-iota-eight-59.vercel.app` |
| `SHARE_BASE_URL` | `https://web-iota-eight-59.vercel.app/share` |
| `VAPID_PUBLIC_KEY` | From `python scripts/generate_vapid.py` |
| `VAPID_PRIVATE_KEY` | Same script (keep secret) |
| `VAPID_CONTACT_EMAIL` | `noreply@setu.health` |

## Wire the Vercel frontend

In `apps/web`, set `API_PROXY_TARGET` to the Railway API origin (no `/api/v1` suffix):

```
API_PROXY_TARGET=https://setu-api-production.up.railway.app
```

Then redeploy web:

```bash
cd apps/web
npx vercel@latest deploy --prod
```

See also `apps/web/DEPLOY.md`.
