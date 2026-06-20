# Opportunity Scoring Methodology

## Purchase Cost Model

All-in cost to acquire and import an item from the **source marketplace** (buy side):

```
purchase_cost =
    item_price_eur
  + shipping_cost_eur
  + platform_buyer_fee
  + currency_conversion_cost
  + import_duty_cost
```

### Default cost assumptions (configurable per marketplace)

| Component | Vinted | Notes |
|-----------|--------|-------|
| Buyer fee | 5% + €0.70 | Vinted protection fee |
| Shipping | €8–15 by country | Seller country → hub |
| FX cost | 0.5% | EUR already native |
| Import to RU | 15% CIF + customs | Simplified flat rate MVP |

```python
platform_buyer_fee = price * marketplace.buyer_fee_pct + fixed_fee
currency_conversion_cost = price * 0.005  # if non-EUR source
import_cost = (price + shipping) * 0.15   # simplified customs
```

Full breakdown stored in `opportunities.cost_breakdown` JSONB.

## Expected Sale Price

Derived from **target marketplace** comparables:

1. Median price of matched Oskelly listings (same brand, category, size ±1)
2. Adjust for condition: `excellent × 1.0`, `good × 0.92`, `fair × 0.85`
3. Apply seller fee deduction for net proceeds

```
expected_sale_gross = median(comparable_prices) * condition_multiplier
seller_fee = expected_sale_gross * marketplace.seller_fee_pct
expected_sale_net = expected_sale_gross - seller_fee
```

## Profit & ROI

```
gross_profit = expected_sale_gross - purchase_cost
net_profit = expected_sale_net - purchase_cost
roi = gross_profit / purchase_cost
```

## Component Scores (0–100)

### ROI Score (weight 0.35)

Piecewise linear mapping:

| ROI | Score |
|-----|-------|
| ≤ 0% | 0 |
| 15% | 30 |
| 30% | 50 |
| 50% | 70 |
| 80% | 90 |
| ≥ 120% | 100 |

```python
roi_score = min(100, max(0, (roi / 1.2) * 100))
```

### Demand Score (weight 0.25)

```
demand_score = weighted_mean([
    brand.demand_score,           # 40%
    category_demand_index,        # 25%
    search_frequency_score,       # 20%
    historical_sales_velocity     # 15%
])
```

Brand demand refreshed nightly from listing volume + sold ratio + search logs.

### Liquidity Score (weight 0.20)

Based on how fast similar items sell on the target market:

```
liquidity_score = weighted_mean([
    sold_listings_ratio * 100,     # 35% — % sold vs active last 90d
    avg_days_to_sell_inverse,      # 35% — faster = higher
    active_inventory_inverse,      # 20% — less saturation = higher
    price_stability                # 10% — stable prices = higher
])
```

Scale: 0 = illiquid, 100 = sells within days.

### Price Gap Score (weight 0.20)

Measures absolute and relative spread:

```
relative_gap = (expected_sale - purchase_cost) / purchase_cost
absolute_gap_eur = expected_sale - purchase_cost

price_gap_score = 0.6 * normalize(relative_gap, 0, 1.0) * 100
                + 0.4 * normalize(absolute_gap_eur, 0, 500) * 100
```

Large absolute gaps on expensive items score higher even if ROI is moderate.

### Risk Score (weight −0.15)

**Higher risk lowers the opportunity score.**

```
risk_score = weighted_mean([
    counterfeit_risk,              # 30% — brand tier based
    condition_uncertainty,         # 25% — vague descriptions
    match_confidence_inverse,      # 25% — 100 - match_confidence
    liquidity_inverse,             # 20% — illiquid = risky
])
```

## Composite Opportunity Score

```
opportunity_score =
    (0.35 × roi_score)
  + (0.25 × demand_score)
  + (0.20 × liquidity_score)
  + (0.20 × price_gap_score)
  − (0.15 × risk_score)
```

Clamped to [0, 100].

## Recommendations

| Score | Recommendation | Meaning |
|-------|----------------|---------|
| ≥ 75 | **BUY** | Strong profit, demand, acceptable risk |
| 50–74 | **WATCH** | Promising but monitor price/risk |
| < 50 | **SKIP** | Insufficient edge or too risky |

Additional hard filters for BUY:
- `roi >= 0.20`
- `match_confidence >= 72`
- `net_profit_eur >= 50`

## Example Calculation

**Maison Margiela Tabi Boots EU 38**

| Field | Value |
|-------|-------|
| Vinted price | €380 |
| Shipping + fees | €62 |
| Import | €66 |
| **Purchase cost** | **€508** |
| Oskelly median | €890 |
| Seller fee (12%) | −€107 |
| **Expected net sale** | **€783** |
| Gross profit | €382 |
| ROI | 75% |
| Match confidence | 87 |
| Brand demand | 82 |

| Component | Score |
|-----------|-------|
| ROI | 62.5 |
| Demand | 82 |
| Liquidity | 68 |
| Price gap | 71 |
| Risk | 24 |

```
opportunity_score = 0.35×62.5 + 0.25×82 + 0.20×68 + 0.20×71 − 0.15×24
                  = 21.9 + 20.5 + 13.6 + 14.2 − 3.6
                  = 66.6 → WATCH
```

With higher liquidity data (score 85): **78.7 → BUY**.

## Recalculation Triggers

- New/updated listing price → re-score affected matches
- Exchange rate update → re-score all open opportunities
- Nightly batch → refresh demand/liquidity from analytics snapshots

## Analytics Rankings

Derived queries on `opportunities` table:

| Ranking | Sort / Filter |
|---------|---------------|
| Top arbitrage | `opportunity_score DESC` |
| Most undervalued | `price_gap_score DESC` |
| Highest ROI | `roi DESC` |
| Fastest moving | `liquidity_score DESC` |
| Highest demand | `demand_score DESC` |
| Best brands this month | `analytics_snapshots` grouped by brand |
| Lowest risk | `risk_score ASC` WHERE `opportunity_score >= 50` |
