# SETU deploy (I2) — public URL for the second-device demo

The demo's share moment needs the doctor brief link to open on a **second
physical device** (the "specialist's phone"). That cannot work on `localhost`.
Deploy the compose stack to a public URL and set the four URL env vars below.

## Option A — AWS EC2 (preferred; doubles as the "scalable cloud" framing)

1. Launch an Ubuntu 22.04 `t3.small` (2 vCPU / 2 GB is enough for the demo).
   Security group: open inbound **80, 443, 3000, 8000** (and 22 for SSH).
2. Install Docker + compose plugin:
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
   sudo usermod -aG docker $USER && newgrp docker   # re-login after
   ```
3. Clone the repo, copy `.env.example` → `.env`, then set the URL vars (below)
   to the instance's public DNS (e.g. `http://ec2-x-x-x-x.compute.amazonaws.com`).
4. Bring it up:
   ```bash
   cd infra && docker compose -f docker-compose.yml up --build -d
   ```
   Postgres is **Supabase** (no local `db` container). Set `DATABASE_URL` +
   `SUPABASE_DB_PASSWORD` per [SUPABASE.md](./SUPABASE.md). Run
   `python scripts/find_pooler.py` from `apps/api` if the pooler region is unknown.

5. Verify:
   ```powershell
   # On Windows (from repo root)
   .\infra\scripts\deploy-checklist.ps1
   # Or with public URLs after DNS is wired:
   $env:PUBLIC_API_URL="http://your-ec2:8000"; $env:PUBLIC_WEB_URL="http://your-ec2:3000"
   .\infra\scripts\deploy-checklist.ps1
   ```

6. (Optional) Demo seed — only if `DEMO_MODE=true`:
   ```bash
   docker compose -f docker-compose.yml exec api python -m app.seed.demo_patient
   ```

7. (Optional but nicer) put nginx or Caddy in front for HTTPS on :443 so the
   brief link is `https://…`. Telegram webhooks REQUIRE https if you use the bot.

## Option B — Tunnel fallback (if a VM is too risky pre-demo)

```bash
cd infra && docker compose -f docker-compose.yml up --build   # local stack
cloudflared tunnel --url http://localhost:8000                 # -> API public URL
cloudflared tunnel --url http://localhost:3000                 # -> web public URL
```
Set the URL vars to the printed `*.trycloudflare.com` URLs and restart the stack
(the web URL must be baked at build time — see the `args:` in docker-compose).

## The four URL env vars (set ALL of them to the deployed origin)

In `infra/../.env` (repo-root `.env`, read by both api and web):

| Var | Set to | Used by |
|-----|--------|---------|
| `PUBLIC_URL` | deployed **API** origin, e.g. `https://api.example.com` | Telegram webhook registration |
| `SHARE_BASE_URL` | deployed **web** origin + `/share`, e.g. `https://app.example.com/share` | share links |
| `BRIEF_BASE_URL` | deployed **web** origin, e.g. `https://app.example.com` | brief/handoff links (Telegram + webchat) |
| `NEXT_PUBLIC_API_BASE_URL` | deployed **API** origin + `/api/v1` | the web app's API client (baked at build) |

Also add the web origin to `CORS_ORIGINS` (comma-separated) so the browser app
can call the API.

After changing `NEXT_PUBLIC_API_BASE_URL`, **rebuild** the web image
(`docker compose ... up --build web`) — Next.js inlines it at build time.

## Supabase (product auth + DB)

When `SUPABASE_ENABLED=true`, also set in `.env`:

- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
- `NEXT_PUBLIC_SUPABASE_*` (rebuild web after changing)
- `DATABASE_URL` → Supabase pooler connection string

Full setup: [SUPABASE.md](./SUPABASE.md).

**Product gate checklist:**

1. Phone login → language onboarding → consent → upload
2. Progress completes → **Marathi/Hindi summary** first → doctor brief
3. Share QR opens on second phone; `?view=specialist` shows **Join video consultation**
4. `pytest -q` passes; `GOOGLE_API_KEY` set for live Gemini path

## Verify the gate (must be on a SECOND device, not curl)

1. Open `BRIEF_BASE_URL/brief/shr_demo_token` in a phone browser (DEMO_MODE on,
   or after a real upload). It must render the brief.
2. Add `?view=specialist` — header should switch to the specialist framing.
3. With `DEMO_MODE=true`, turn the laptop's wifi off and confirm the seeded
   patient still renders (zero external dependency).

## Telegram webhook (only if demoing the bot — note: Telegram is down in IN;
the web app is the demo channel)

```bash
docker compose -f docker-compose.yml exec api python scripts/register_telegram_webhook.py
```
Requires `PUBLIC_URL` (https) + `TELEGRAM_BOT_TOKEN` set in `.env`.
