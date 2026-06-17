# SETU demo smoke checks — run against a running API (local or staging).
param(
    [string]$ApiBase = $(if ($env:NEXT_PUBLIC_API_BASE_URL) { $env:NEXT_PUBLIC_API_BASE_URL } else { "http://127.0.0.1:8000/api/v1" })
)

$ErrorActionPreference = "Stop"
$ok = $true

function Check([string]$label, [bool]$pass) {
    if ($pass) { Write-Host "[OK] $label" -ForegroundColor Green }
    else { Write-Host "[FAIL] $label" -ForegroundColor Red; $script:ok = $false }
}

Write-Host "SETU demo smoke" -ForegroundColor Cyan
Write-Host "API: $ApiBase"
Write-Host ""

try {
    $health = Invoke-RestMethod -Uri ($ApiBase -replace "/api/v1$", "") + "/health" -TimeoutSec 10
    Check "API health" ($health.status -eq "ok")
} catch {
    Check "API health" $false
}

try {
    $openapi = Invoke-RestMethod -Uri ($ApiBase -replace "/api/v1$", "") + "/openapi.json" -TimeoutSec 15
    $paths = $openapi.paths.PSObject.Properties.Name
    foreach ($p in @(
        "/api/v1/encounters/{encounter_id}/prescriptions",
        "/api/v1/appointments/{appointment_id}/visit-summary",
        "/api/v1/notifications",
        "/api/v1/admin/appointments"
    )) {
        Check "OpenAPI path $p" ($paths -contains $p)
    }
} catch {
    Check "OpenAPI fetch" $false
}

if (-not $ok) { exit 1 }
Write-Host ""
Write-Host "Smoke checks passed. For full E2E: patient login -> book -> doctor accept -> Rx -> summary." -ForegroundColor Green
