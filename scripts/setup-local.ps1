# Lux Arbitrage — local setup (no Docker)
# Run from project root: .\scripts\setup-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Lux Arbitrage local setup" -ForegroundColor Cyan

# Python
$venv = Join-Path $Root "backend\.venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating Python venv..."
    python -m venv $venv
}
$py = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"

Write-Host "Installing Python dependencies..."
& $pip install -q -r (Join-Path $Root "backend\requirements.txt")

# Env
if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host "Created .env from .env.example"
}
$feEnv = Join-Path $Root "frontend\.env.local"
if (-not (Test-Path $feEnv)) {
    Copy-Item (Join-Path $Root "frontend\.env.local.example") $feEnv
    Write-Host "Created frontend/.env.local"
}

# Node
Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $Root "frontend")
npm install --silent
Pop-Location

# Database
Write-Host "Initializing SQLite database..."
Push-Location (Join-Path $Root "backend")
& $py -c "import asyncio; from app.database import init_db; asyncio.run(init_db()); print('DB ready')"
Pop-Location

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "  Start dev:  .\scripts\start-local.ps1"
Write-Host "  Seed data:  .\scripts\run-scrape.ps1"
Write-Host "  API docs:   http://localhost:8000/docs"
