# AWS / public deploy verification checklist (PS "scalable cloud")
# Run on the EC2 instance after `docker compose up -d`, or locally before deploy.

param(
    [string]$PublicWeb = $env:PUBLIC_WEB_URL,
    [string]$PublicApi = $env:PUBLIC_API_URL
)

$ErrorActionPreference = "Continue"
$ok = $true

function Check([string]$label, [bool]$pass) {
    if ($pass) { Write-Host "[OK] $label" -ForegroundColor Green }
    else { Write-Host "[FAIL] $label" -ForegroundColor Red; $script:ok = $false }
}

Write-Host "SETU deploy checklist" -ForegroundColor Cyan
Write-Host ""

# Local health (when running on server)
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    Check "API /health" ($health.status -eq "ok")
    Check "Database" ($health.database -eq "ok")
} catch {
    Check "API /health (local :8000)" $false
}

# Env file presence
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    $content = Get-Content $envFile -Raw
    foreach ($var in @("DATABASE_URL", "SUPABASE_DB_PASSWORD", "GOOGLE_API_KEY", "NEXT_PUBLIC_API_BASE_URL", "BRIEF_BASE_URL", "SHARE_BASE_URL")) {
        Check ".env has $var" ($content -match "$var=.+")
    }
} else {
    Check "repo-root .env exists" $false
}

if ($PublicApi) {
    try {
        $h = Invoke-RestMethod -Uri "$PublicApi/health" -TimeoutSec 10
        Check "Public API $PublicApi/health" ($h.status -eq "ok")
    } catch {
        Check "Public API reachable" $false
    }
}

if ($PublicWeb) {
    try {
        $r = Invoke-WebRequest -Uri $PublicWeb -UseBasicParsing -TimeoutSec 10
        Check "Public web $PublicWeb" ($r.StatusCode -eq 200)
    } catch {
        Check "Public web reachable" $false
    }
}

Write-Host ""
if ($ok) {
    Write-Host "Checklist passed. Second-device gate: open BRIEF_BASE_URL/brief/{token}?view=specialist on a phone." -ForegroundColor Green
    exit 0
}
Write-Host "Fix failures above, then rebuild web if NEXT_PUBLIC_* changed: docker compose up --build web" -ForegroundColor Yellow
exit 1
