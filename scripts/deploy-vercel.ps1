# Deploy frontend to Vercel
# Prerequisites: run `vercel login` once, then from project root:

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "frontend")

if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "Install Vercel CLI: npm install -g vercel" -ForegroundColor Red
    exit 1
}

Write-Host "Deploying to Vercel (production)..." -ForegroundColor Cyan
Write-Host "Root directory: frontend (run from frontend/)"
vercel --prod --yes
