# Lux Arbitrage — Folder Structure

```
lux-arbitrage/
├── README.md
├── .env.example
├── docker-compose.yml
├── .gitignore
│
├── docs/
│   ├── ARCHITECTURE.md       # System design, data flow, scalability
│   ├── DATABASE.md           # Full schema documentation
│   ├── API.md                # REST API specification
│   ├── MATCHING_ENGINE.md    # Hybrid matching algorithm
│   ├── SCORING.md            # Opportunity scoring methodology
│   └── MVP_ROADMAP.md        # Phased delivery plan
│
├── infrastructure/
│   └── postgres/
│       └── init.sql          # DB extensions
│
├── scripts/
│   └── (dev utilities)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── app/
│       ├── main.py           # FastAPI entry point
│       ├── config.py         # Settings (pydantic-settings)
│       ├── database.py       # Async SQLAlchemy engine
│       ├── dependencies.py   # Auth dependencies
│       │
│       ├── models/           # SQLAlchemy ORM models
│       │   ├── user.py
│       │   ├── marketplace.py
│       │   ├── brand.py
│       │   ├── listing.py
│       │   ├── match.py
│       │   ├── opportunity.py
│       │   ├── alert.py
│       │   └── analytics.py
│       │
│       ├── schemas/          # Pydantic request/response schemas
│       │   └── common.py
│       │
│       ├── api/
│       │   └── routes.py     # All REST endpoints
│       │
│       ├── services/
│       │   ├── normalization.py  # Brand, size, title cleaning
│       │   ├── currency.py       # FX conversion
│       │   ├── matching.py         # Match confidence scoring
│       │   ├── scoring.py          # Opportunity scoring
│       │   └── pipeline.py         # Ingest → match → score
│       │
│       ├── scrapers/
│       │   ├── base.py         # MarketplaceAdapter ABC
│       │   ├── vinted.py       # Vinted mock adapter
│       │   └── oskelly.py      # Oskelly mock adapter
│       │
│       ├── workers/
│       │   ├── celery_app.py   # Celery config + beat schedule
│       │   └── tasks.py        # Background tasks
│       │
│       ├── core/
│       │   ├── constants.py    # Brand aliases, size maps, weights
│       │   └── security.py     # JWT + bcrypt
│       │
│       └── scripts/
│           └── seed.py         # Demo data seeder
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.js
    └── src/
        ├── lib/
        │   ├── api.ts          # API client
        │   └── utils.ts        # Formatting helpers
        ├── components/
        │   ├── opportunity-card.tsx
        │   ├── stat-card.tsx
        │   ├── score-bar.tsx
        │   └── refresh-button.tsx
        └── app/
            ├── layout.tsx      # Sidebar navigation
            ├── page.tsx        # Opportunity dashboard
            ├── opportunities/[id]/page.tsx
            ├── brands/page.tsx
            ├── brands/[slug]/page.tsx
            ├── rankings/page.tsx
            └── alerts/page.tsx
```

## Extension Points (Multi-Marketplace)

Add new marketplaces by:

1. Create `backend/app/scrapers/{marketplace}.py` implementing `MarketplaceAdapter`
2. Insert row in `marketplaces` table
3. Register adapter in `pipeline.py`
4. Update matching direction rules for buy/sell market pairs

Supported future slugs: `vestiaire`, `grailed`, `therealreal`, `depop`, `avito`
