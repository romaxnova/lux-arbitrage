# Start API + frontend locally (no Docker)
# Run from project root: .\scripts\start-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$venv = Join-Path $Root "backend\.venv"
$py = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Run .\scripts\setup-local.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Starting Lux Arbitrage (API :8000, frontend :3000)..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C in each window to stop." -ForegroundColor DarkGray

$apiCmd = "Set-Location '$Root\backend'; & '$py' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
$feCmd = "Set-Location '$Root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $feCmd

Write-Host ""
Write-Host "  Dashboard: http://localhost:3000"
Write-Host "  API:       http://localhost:8000/health"
