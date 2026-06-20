# MVP Roadmap

## Phase 1 — Foundation (Weeks 1–2) ✅ This repo

**Goal**: Runnable platform with mock data proving the full pipeline.

- [x] Docker Compose stack (Postgres, Redis, Meilisearch, MinIO, API, Worker, Frontend)
- [x] Database schema + Alembic migrations
- [x] Brand normalization (20+ luxury brands with aliases)
- [x] Size normalization (EU/US/UK/IT clothing + shoes)
- [x] Currency conversion (Frankfurter API)
- [x] Mock Vinted + Oskelly scrapers with realistic listings
- [x] Hybrid matching engine (fuzzy text + rules)
- [x] Opportunity scoring engine
- [x] REST API (auth, opportunities, brands, alerts, watchlists)
- [x] Dashboard UI (opportunities, brand intel, detail pages)
- [x] Seed script with demo opportunities

**Exit criteria**: `docker compose up` → dashboard shows ranked BUY/WATCH/SKIP opportunities.

---

## Phase 2 — Live Data (Weeks 3–4) ✅ Implemented

**Goal**: Real listing ingestion from Vinted and Oskelly.

- [x] Vinted internal catalog API adapter (session bootstrap + brand lookup)
- [x] Oskelly Nuxt catalog parser adapter
- [x] Celery beat schedules (hourly by default)
- [x] Listing upsert + deduplication
- [x] Stale listing cleanup (72h default)
- [x] Meilisearch index sync on ingest
- [x] Price history tracking on price changes
- [ ] Image download + S3 storage pipeline (deferred — uses marketplace CDN URLs)
- [ ] Sold listing tracking on Oskelly (partial — sold state when available)

**Exit criteria**: 1,000+ real listings, 50+ matched opportunities — run full pipeline after deploy.

---

## Phase 3 — Intelligence (Weeks 5–6)

**Goal**: Improve match quality and scoring accuracy.

- [ ] CLIP image embedding service
- [ ] Sentence-transformer title embeddings
- [ ] Sold listing tracking on Oskelly (liquidity signals)
- [ ] Brand demand scoring from historical data
- [ ] Analytics nightly snapshots (brand/category trends)
- [ ] Manual match verification UI (admin)

**Exit criteria**: Match precision > 80% on 100-item eval set.

---

## Phase 4 — User Features (Weeks 7–8)

**Goal**: Production-ready user experience.

- [ ] Email/Telegram alert notifications
- [ ] Advanced filter presets ("Margiela shoes EU 38–40")
- [ ] Watchlist with price change tracking
- [ ] Export opportunities to CSV
- [ ] User settings (default marketplaces, fee overrides)

---

## Phase 5 — Scale & Expand (Weeks 9–12)

**Goal**: Multi-marketplace support and production deployment.

- [ ] Vestiaire Collective adapter
- [ ] Grailed adapter
- [ ] AWS deployment (ECS + RDS + ElastiCache + S3)
- [ ] Read replicas + connection pooling (PgBouncer)
- [ ] pgvector for embedding search at scale
- [ ] API rate limiting + monitoring (Datadog/Sentry)
- [ ] Horizontal Celery workers

**Exit criteria**: Support 100K+ listings, < 200ms API p95.

---

## Phase 6 — Advanced (Future)

- ML match classifier trained on verified pairs
- Predictive pricing (time-series forecast)
- Portfolio tracker (items bought/sold)
- Mobile app (React Native)
- Depop, The RealReal, Avito adapters
- Multi-direction arbitrage (not just Vinted → Oskelly)

---

## Priority Brands (Launch)

| Brand | Category focus |
|-------|----------------|
| Prada | Bags, shoes |
| Miu Miu | Bags, accessories |
| Maison Margiela | Shoes (Tabi), bags |
| Balenciaga | Sneakers, outerwear |
| Rick Owens | Footwear, leather |
| Diesel | Denim, accessories |
| Acne Studios | Denim, knits |
| Chrome Hearts | Jewelry, eyewear |

---

## Success Metrics

| Metric | MVP target | 6-month target |
|--------|------------|----------------|
| Active listings | 500 | 100,000 |
| Match rate | 10% | 25% |
| Opportunities/day | 20 | 500 |
| Avg opportunity score (BUY) | > 70 | > 75 |
| API uptime | 95% | 99.5% |
| Match precision | 70% | 85% |
