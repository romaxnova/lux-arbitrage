# Docker-based dev stack (optional).
# For native local dev without Docker, use: .\scripts\start-local.ps1

# Start Lux Arbitrage — checks Docker, waits for engine, then brings up stack

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

function Test-DockerEngine {
    docker info 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Start-DockerDesktop {
    $paths = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
            Start-Process $p
            return $true
        }
    }
    return $false
}

Write-Host "Lux Arbitrage — startup" -ForegroundColor Cyan

if (-not (Test-DockerEngine)) {
    Write-Host "Docker engine is not running." -ForegroundColor Yellow
    if (-not (Start-DockerDesktop)) {
        Write-Host "ERROR: Docker Desktop not installed. Install from https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
        Write-Host "Or run without Docker: .\scripts\start-local.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "Waiting for Docker engine (up to 120s)..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        if (Test-DockerEngine) { $ready = $true; break }
        Write-Host "." -NoNewline
    }
    Write-Host ""
    if (-not $ready) {
        Write-Host "ERROR: Docker engine did not start in time. Open Docker Desktop manually, wait until it says Running, then re-run this script." -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker engine ready." -ForegroundColor Green
}

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

Write-Host "Building and starting containers..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Waiting for API health..." -ForegroundColor Yellow
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $healthy = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}
if (-not $healthy) {
    Write-Host "API not healthy yet — check: docker compose logs api" -ForegroundColor Yellow
} else {
    Write-Host "API is healthy." -ForegroundColor Green
}

Write-Host "Running initial scrape (live Vinted + Oskelly, may take several minutes)..." -ForegroundColor Yellow
docker compose exec -T api python -m app.scripts.seed
if ($LASTEXITCODE -ne 0) {
    Write-Host "Seed failed — you can retry: docker compose exec api python -m app.scripts.seed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Ready!" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:3000"
Write-Host "  API docs:  http://localhost:8000/docs"
Write-Host "  Stats:     http://localhost:8000/api/v1/market/stats"
