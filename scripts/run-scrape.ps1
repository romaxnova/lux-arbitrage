# Run live scrape + matching pipeline (takes a few minutes)
# Run from project root: .\scripts\run-scrape.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $Root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "Run .\scripts\setup-local.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Running scrape pipeline (Vinted + Oskelly)..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "backend")
& $py -m app.scripts.seed
Pop-Location
