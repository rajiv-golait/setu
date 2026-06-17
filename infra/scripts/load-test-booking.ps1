# Load test: concurrent appointment slot booking
# Requires API running at $env:API_BASE (default http://localhost:8000)
# Usage: .\infra\scripts\load-test-booking.ps1 -Requests 20

param(
    [string]$ApiBase = "http://localhost:8000/api/v1",
    [int]$Requests = 10,
    [string]$ProviderId = "",
    [string]$PatientToken = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProviderId) {
    Write-Host "Set -ProviderId to an approved provider with generated slots."
    exit 1
}

$headers = @{}
if ($PatientToken) {
    $headers["Authorization"] = "Bearer $PatientToken"
}

# Fetch first available slot
$slots = Invoke-RestMethod -Uri "$ApiBase/providers/$ProviderId/slots" -Headers $headers
$slot = $slots | Where-Object { $_.status -eq "available" } | Select-Object -First 1
if (-not $slot) {
    Write-Host "No available slots for provider $ProviderId"
    exit 1
}

Write-Host "Hammering slot $($slot.id) with $Requests parallel booking attempts..."

$jobs = 1..$Requests | ForEach-Object {
    Start-Job -ScriptBlock {
        param($base, $hdrs, $body)
        try {
            $r = Invoke-WebRequest -Uri "$base/appointments" -Method POST -Headers $hdrs `
                -ContentType "application/json" -Body ($body | ConvertTo-Json) -UseBasicParsing
            return @{ status = $r.StatusCode; ok = $true }
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
            return @{ status = $code; ok = $false }
        }
    } -ArgumentList $ApiBase, $headers, @{
        specialty = "General physician"
        provider_id = $ProviderId
        slot_id = $slot.id
    }
}

$results = $jobs | Wait-Job | Receive-Job
$jobs | Remove-Job

$success = ($results | Where-Object { $_.status -eq 201 -or $_.status -eq 200 }).Count
$conflict = ($results | Where-Object { $_.status -eq 409 }).Count
$other = $Requests - $success - $conflict

Write-Host "Results: success=$success conflict=$conflict other=$other"
if ($success -gt 1) {
    Write-Host "FAIL: double-book detected" -ForegroundColor Red
    exit 1
}
Write-Host "PASS: at most one booking succeeded" -ForegroundColor Green
