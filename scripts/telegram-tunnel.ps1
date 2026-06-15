# Start Cloudflare quick tunnels for SETU Telegram dev.
# - API  (8000) -> PUBLIC_URL / webhook
# - Web  (3000) -> BRIEF_BASE_URL (links in Telegram messages)
#
# Usage: .\scripts\telegram-tunnel.ps1
# Then update .env PUBLIC_URL + BRIEF_BASE_URL from the printed URLs,
# restart api: docker compose -f infra/docker-compose.yml up -d api
# Register webhook: docker compose -f infra/docker-compose.yml exec api python scripts/register-telegram-webhook.py

Write-Host "Starting API tunnel (localhost:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "npx --yes cloudflared@latest tunnel --url http://localhost:8000 --no-autoupdate"
)

Start-Sleep -Seconds 2

Write-Host "Starting Web tunnel (localhost:3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "npx --yes cloudflared@latest tunnel --url http://localhost:3000 --no-autoupdate"
)

Write-Host ""
Write-Host "Two tunnel windows opened. Copy the https://*.trycloudflare.com URLs:" -ForegroundColor Yellow
Write-Host "  PUBLIC_URL      = API tunnel URL"
Write-Host "  BRIEF_BASE_URL  = Web tunnel URL"
Write-Host ""
Write-Host "Then run:"
Write-Host "  docker compose -f infra/docker-compose.yml up -d api"
Write-Host "  docker compose -f infra/docker-compose.yml exec api sh -c `"PYTHONPATH=/app python scripts/register_telegram_webhook.py`""
