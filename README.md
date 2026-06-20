# Lux Arbitrage Intelligence Platform

Data-driven arbitrage engine for luxury fashion resale between **Vinted** (Europe) and **Oskelly** (Russia).

## Quick start (local — no Docker)

Requires **Python 3.11+** and **Node.js 18+** on this machine.

```powershell
cd lux-arbitrage
.\scripts\setup-local.ps1    # venv, npm install, init SQLite DB
.\scripts\start-local.ps1    # API :8000 + dashboard :3000
.\scripts\run-scrape.ps1     # live Vinted + Oskelly scrape (few min)
```

| URL | Service |
|-----|---------|
| http://localhost:3000 | Dashboard |
| http://localhost:8000/docs | API docs |
| http://localhost:8000/health | Health check |

Data is stored in `data/lux_arbitrage.db` (SQLite). Copy `.env.example` → `.env` to customize.

## Deploy to Vercel (frontend)

The Next.js dashboard deploys to Vercel; the API runs separately (Railway, Render, or your PC).

See **[docs/DEPLOY_VERCEL.md](docs/DEPLOY_VERCEL.md)** for full steps.

Set on Vercel: `NEXT_PUBLIC_API_URL=https://your-api-host`

## Tech stack

| Layer | Local | Production |
|-------|-------|------------|
| Frontend | Next.js 15 | Vercel |
| Backend | FastAPI + uvicorn | Railway / Render / PC |
| Database | SQLite | PostgreSQL (optional) |
| Search / jobs | Off (MVP) | Meilisearch + Celery (optional) |

Docker Compose is **optional** — see `docker-compose.yml` if you want Postgres/Redis/Meilisearch in containers.

## Project structure

```
lux-arbitrage/
├── backend/          # FastAPI, scrapers, matching engine
├── frontend/         # Next.js dashboard (Vercel root)
├── data/             # SQLite DB (gitignored)
├── scripts/          # setup-local.ps1, start-local.ps1, run-scrape.ps1
└── docs/             # Architecture, API, deployment
```

## Documentation

- [Deploy to Vercel](docs/DEPLOY_VERCEL.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [API Specification](docs/API.md)
- [Matching Engine](docs/MATCHING_ENGINE.md)
- [Opportunity Scoring](docs/SCORING.md)

## License

Proprietary — internal use.
