# Apply SETU Alembic migrations to Supabase Postgres.
# Usage (from repo root):
#   $env:SUPABASE_DB_PASSWORD = "your-db-password"
#   .\infra\scripts\migrate-supabase.ps1
#
# Or:
#   .\infra\scripts\migrate-supabase.ps1 -Password "your-db-password"

param(
    [string]$Password = $env:SUPABASE_DB_PASSWORD,
    [string]$ProjectRef = "sevwzahlsunwqbiowbcx"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ApiDir = Join-Path $RepoRoot "apps\api"
$Alembic = Join-Path $ApiDir ".venv\Scripts\alembic.exe"

if (-not $Password) {
    Write-Host @"
Missing database password.

1. Supabase Dashboard → Project Settings → Database
2. Copy your database password (or reset it)
3. Run:
     `$env:SUPABASE_DB_PASSWORD = 'YOUR_PASSWORD'
     .\infra\scripts\migrate-supabase.ps1

Alternative: paste infra/supabase-schema.sql into SQL Editor (no password needed in terminal).
"@ -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $Alembic)) {
    Write-Host "API venv not found. Run: cd apps\api; python -m venv .venv; .\.venv\Scripts\pip install -e `".[dev]`"" -ForegroundColor Red
    exit 1
}

# Direct connection (port 5432) — required for DDL/migrations on Supabase.
$DbUrl = "postgresql+psycopg://postgres:${Password}@db.${ProjectRef}.supabase.co:5432/postgres?sslmode=require"
$PoolUrl = "postgresql+psycopg://postgres.${ProjectRef}:${Password}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

Write-Host "Running alembic upgrade head against Supabase ($ProjectRef)..." -ForegroundColor Cyan
$env:DATABASE_URL = $DbUrl
Push-Location $ApiDir
try {
    & $Alembic upgrade head
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Migrations applied. Update your .env files:" -ForegroundColor Green
Write-Host "  DATABASE_URL=$PoolUrl"
Write-Host ""
Write-Host "Also set the same DATABASE_URL in apps\api\.env if you run uvicorn locally."
Write-Host "Restart the API after changing DATABASE_URL."
