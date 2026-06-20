# API Specification

Base URL: `http://localhost:8000/api/v1`

Authentication: Bearer JWT in `Authorization` header.

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user profile |

### POST /auth/login

**Request**
```json
{ "email": "trader@example.com", "password": "secret" }
```

**Response**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Opportunities

| Method | Path | Description |
|--------|------|-------------|
| GET | `/opportunities` | Ranked opportunity list |
| GET | `/opportunities/{id}` | Full opportunity detail |
| GET | `/opportunities/rankings/{type}` | Curated rankings |

### GET /opportunities

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| brand | string | Filter by brand slug |
| category | string | Filter by category |
| size | string | Normalized size |
| country | string | Seller country (ISO-2) |
| min_profit | number | Minimum gross profit EUR |
| min_roi | number | Minimum ROI (0.5 = 50%) |
| min_demand | number | Minimum demand score |
| max_risk | number | Maximum risk score |
| recommendation | string | BUY, WATCH, SKIP |
| sort | string | score, roi, profit, demand, risk |
| page | int | Default 1 |
| page_size | int | Default 20, max 100 |

**Response**
```json
{
  "items": [
    {
      "id": "uuid",
      "opportunity_score": 82.4,
      "recommendation": "BUY",
      "roi": 0.67,
      "gross_profit_eur": 420.0,
      "net_profit_eur": 385.0,
      "demand_score": 78.0,
      "liquidity_score": 65.0,
      "risk_score": 22.0,
      "purchase_listing": {
        "title": "Maison Margiela Tabi boots",
        "price_eur": 380.0,
        "marketplace": "vinted",
        "url": "https://...",
        "image_urls": ["https://..."]
      },
      "sale_listing": {
        "title": "Maison Margiela Tabi",
        "price_eur": 890.0,
        "marketplace": "oskelly",
        "url": "https://..."
      },
      "brand": { "name": "Maison Margiela", "slug": "maison-margiela" }
    }
  ],
  "total": 142,
  "page": 1,
  "page_size": 20
}
```

### GET /opportunities/rankings/{type}

Types: `top`, `undervalued`, `highest_roi`, `fastest_moving`, `highest_demand`, `lowest_risk`

---

## Listings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/listings` | Search listings |
| GET | `/listings/{id}` | Listing detail |
| GET | `/listings/{id}/price-history` | Price trend |

---

## Products

| Method | Path | Description |
|--------|------|-------------|
| GET | `/products` | Product catalog search |
| GET | `/products/{id}` | Product with cross-market listings |

---

## Brand Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/brands` | All tracked brands |
| GET | `/brands/{slug}` | Brand intelligence page |
| GET | `/brands/{slug}/analytics` | Time-series metrics |

### GET /brands/{slug}

```json
{
  "brand": { "name": "Prada", "slug": "prada", "tier": "luxury" },
  "avg_vinted_price_eur": 485.0,
  "avg_oskelly_price_eur": 720.0,
  "median_spread_eur": 235.0,
  "median_roi": 0.42,
  "demand_trend": "rising",
  "liquidity_trend": "stable",
  "top_categories": [
    { "category": "bags", "median_roi": 0.55, "opportunity_count": 23 }
  ],
  "active_opportunities": 47
}
```

---

## Alerts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts` | User alerts |
| POST | `/alerts` | Create alert |
| PATCH | `/alerts/{id}` | Update alert |
| DELETE | `/alerts/{id}` | Delete alert |

### POST /alerts

```json
{
  "name": "High ROI Margiela",
  "rule_type": "roi",
  "conditions": {
    "roi_min": 0.8,
    "brand_slug": "maison-margiela"
  }
}
```

Supported `rule_type` values: `roi`, `price_gap`, `brand_price`, `category_deal`

---

## Watchlists

| Method | Path | Description |
|--------|------|-------------|
| GET | `/watchlists` | User watchlist |
| POST | `/watchlists` | Add item |
| DELETE | `/watchlists/{id}` | Remove item |

---

## Market Data

| Method | Path | Description |
|--------|------|-------------|
| GET | `/market/exchange-rates` | Current FX rates |
| GET | `/market/marketplaces` | Marketplace config |
| GET | `/market/stats` | Platform-wide stats |

---

## Admin

Requires `is_superuser`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/scrape/trigger` | Trigger scrape job |
| POST | `/admin/matching/run` | Run matching batch |
| POST | `/admin/scoring/run` | Recalculate opportunities |
| GET | `/admin/jobs` | Celery job status |

---

## Error Format

```json
{
  "detail": "Human-readable message",
  "code": "NOT_FOUND"
}
```

HTTP status codes: 400 validation, 401 unauthorized, 403 forbidden, 404 not found, 422 unprocessable.
