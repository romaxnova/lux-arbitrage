# Deploying Lux Arbitrage

## Architecture on Vercel

| Component | Host | Notes |
|-----------|------|-------|
| **Frontend** (Next.js) | **Vercel** | Dashboard, static assets |
| **API** (FastAPI) | Railway / Render / Fly.io / your PC | Scrapers, DB, matching |
| **Database** | SQLite (local) or PostgreSQL (prod) | Neon, Supabase, Railway |
| Meilisearch, Redis, Celery | Optional | Not required for MVP |

Vercel runs the Next.js app only. The FastAPI backend cannot run on Vercel serverless as-is (long-running scrapers, SQLite file, background jobs).

## 1. Deploy frontend to Vercel

1. Push the repo to GitHub.
2. Import the project in [Vercel](https://vercel.com/new).
3. Set **Root Directory** to `frontend`.
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = your public API URL (e.g. `https://lux-api.railway.app`)
5. Deploy.

`frontend/vercel.json` is already configured for the Next.js framework.

After deploy, add your Vercel URL to the API CORS list:

```env
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

The API also allows any `https://*.vercel.app` origin via regex.

## 2. Host the API

### Option A — Railway / Render (recommended for production)

1. Deploy `backend/` as a Python web service.
2. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set `DATABASE_URL` to PostgreSQL (`postgresql+asyncpg://...`).
4. Set `SECRET_KEY`, `CORS_ORIGINS`, scraper flags as needed.

### Option B — Keep API on your PC (dev / personal use)

1. Run `.\scripts\start-local.ps1`.
2. Expose port 8000 with [ngrok](https://ngrok.com/) or Cloudflare Tunnel.
3. Set `NEXT_PUBLIC_API_URL` on Vercel to the tunnel URL.

## 3. Local development (no Docker)

```powershell
.\scripts\setup-local.ps1   # once
.\scripts\start-local.ps1   # API + frontend
.\scripts\run-scrape.ps1    # live data
```

- SQLite DB: `data/lux_arbitrage.db`
- API: http://localhost:8000
- Dashboard: http://localhost:3000

## 4. Docker (optional)

Docker Compose is still available for full stack (Postgres, Redis, Meilisearch). See [DEPLOY.md](DEPLOY.md).
