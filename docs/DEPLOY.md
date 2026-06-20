# Deploying Lux Arbitrage MVP (Phase 2)

Phase 2 ships **live Vinted + Oskelly scrapers** with upsert ingestion, price history, stale listing cleanup, and Meilisearch sync.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- 4 GB RAM minimum
- Outbound HTTPS to `vinted.fr` and `oskelly.ru`

## Quick deploy (single server)

```bash
cp .env.example .env
# Edit SECRET_KEY and POSTGRES_PASSWORD for production

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec api python -m app.scripts.seed
```

Open:
- Dashboard: http://YOUR_SERVER:3000
- API docs: http://YOUR_SERVER:8000/docs

## What runs

| Service | Role |
|---------|------|
| `postgres` | Primary data store |
| `redis` | Celery broker + cache |
| `meilisearch` | Full-text search index |
| `api` | FastAPI REST API |
| `worker` | Celery scraper + matching + scoring |
| `beat` | Scheduled scrape every 60 min (configurable) |
| `frontend` | Next.js dashboard |

## Data pipeline (automatic)

Every `SCRAPER_INTERVAL_MINUTES` (default 60):

1. **Ingest** — Vinted catalog API + Oskelly Nuxt catalog pages
2. **Upsert** — create/update listings, append `price_history` on price change
3. **Cleanup** — deactivate listings not seen in `SCRAPER_STALE_HOURS` (default 72h)
4. **Match** — hybrid engine links Vinted buy → Oskelly sell
5. **Score** — opportunity scores + BUY/WATCH/SKIP
6. **Index** — sync to Meilisearch

Manual trigger: `POST /api/v1/admin/scrape/trigger` or **Refresh Data** in the dashboard.

## Scraper configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VINTED_DOMAIN` | `fr` | Vinted TLD (fr, de, it, …) |
| `VINTED_MAX_PAGES` | `3` | Pages per brand (~144 items max) |
| `VINTED_MIN_PRICE_EUR` | `40` | Skip cheap listings |
| `OSKELLY_MAX_PAGES` | `3` | Catalog pages per brand |
| `OSKELLY_MIN_PRICE_RUB` | `5000` | Skip cheap listings |
| `SCRAPER_LISTINGS_PER_QUERY` | `30` | Cap per brand per marketplace |

## Railway / cloud deploy

1. Push repo to GitHub
2. Create Railway project from `docker-compose.yml`
3. Set environment variables from `.env.example`
4. Expose ports `3000` (frontend) and `8000` (api)
5. Run seed: `railway run python -m app.scripts.seed`

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/market/stats
```

Expected after first scrape: `active_listings` > 100, `opportunities` > 0.

## Troubleshooting

**Vinted returns 403** — Vinted uses DataDome. The scraper bootstraps cookies from the catalog page. If blocked, reduce `VINTED_MAX_PAGES`, increase scrape interval, or add a residential proxy (future).

**Oskelly returns empty** — Check `oskelly.ru` is reachable from your server. Russian marketplace may need non-blocked IP.

**No opportunities** — Matching requires same brand + category + price gap. Run matching manually: `POST /api/v1/admin/matching/run`.

## Legal note

Scraping must comply with each marketplace's Terms of Service. This MVP is for internal arbitrage research. Rate limits are enforced (0.5–0.8 req/s per marketplace).
