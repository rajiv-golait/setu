# Deploy `apps/web` to Vercel

## Live project

| | URL |
|---|---|
| Production | https://web-iota-eight-59.vercel.app |
| Vercel dashboard | https://vercel.com/rajiv-golait-s-projects/web |

The CLI is linked to this folder (`apps/web`). Redeploy from here:

```bash
cd apps/web
npx vercel@latest deploy --prod
```

## Required: API URL

The frontend calls `NEXT_PUBLIC_API_BASE_URL` (see `src/lib/constants.ts`). Without it, the build defaults to `http://localhost:8000/api/v1`, which **does not work** from a deployed browser.

1. Deploy the API somewhere public (EC2, Railway, Render, Fly.io, etc.) — see `infra/DEPLOY.md`.
2. In [Vercel → web → Settings → Environment Variables](https://vercel.com/rajiv-golait-s-projects/web/settings/environment-variables), add:

   | Name | Example |
   |------|---------|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://api.yourdomain.com/api/v1` |

   Apply to **Production**, **Preview**, and **Development**.

3. **Redeploy** after changing this variable (Next.js inlines it at build time).

## Required: CORS on the API

Add your Vercel origin to the API’s `CORS_ORIGINS` (repo-root `.env` on the server):

```
CORS_ORIGINS=http://localhost:3000,https://web-iota-eight-59.vercel.app
```

Also set (on the API host):

```
BRIEF_BASE_URL=https://web-iota-eight-59.vercel.app
SHARE_BASE_URL=https://web-iota-eight-59.vercel.app/share
```

Restart/redeploy the API after changing these.

## Git auto-deploy (recommended)

1. Open https://vercel.com/rajiv-golait-s-projects/web/settings/git
2. Connect **GitHub** → `rajiv-golait/setu`
3. Set **Root Directory** to `apps/web`
4. Framework preset: **Next.js** (auto-detected)
5. Add `NEXT_PUBLIC_API_BASE_URL` in env vars, then redeploy

Every push to `main` will deploy production; other branches get preview URLs.

## Verify

1. Open https://web-iota-eight-59.vercel.app — home should load (not stuck on “Loading…” once API + CORS are set).
2. Upload a document → progress → brief.
3. Open `/brief/shr_demo_token` or a real share token on a second device.

## Admin login (production)

`/admin/login` uses **Supabase email/password**. The dev bootstrap API (`POST /auth/dev/ensure-admin`) is disabled when Railway has `PRODUCTION=true`.

1. **Create the admin once** (local machine, prod Supabase keys in `apps/api/.env`):

   ```bash
   cd apps/api
   python scripts/create_dev_admin.py
   ```

   Or Supabase Dashboard → Authentication → Users: create the admin user with `app_metadata.role` = `admin`.

2. Vercel env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ENABLED=true`.

3. Sign in at `/admin/login`.
