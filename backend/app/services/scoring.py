from decimal import Decimal

from app.core.constants import SCORING_WEIGHTS
from app.models import Brand, Listing, Marketplace, Match


def clamp_score(value: float) -> Decimal:
    return Decimal(str(max(0.0, min(100.0, value)))).quantize(Decimal("0.01"))


def compute_roi_score(roi: Decimal) -> Decimal:
    roi_float = float(roi)
    if roi_float <= 0:
        return Decimal("0.00")
    score = min(100.0, (roi_float / 1.2) * 100)
    return clamp_score(score)


def compute_price_gap_score(gross_profit: Decimal, purchase_cost: Decimal) -> Decimal:
    if purchase_cost <= 0:
        return Decimal("0.00")
    relative = float(gross_profit / purchase_cost)
    absolute = float(gross_profit)
    rel_score = min(100.0, max(0.0, relative / 1.0 * 100)) * 0.6
    abs_score = min(100.0, max(0.0, absolute / 500 * 100)) * 0.4
    return clamp_score(rel_score + abs_score)


def compute_liquidity_score(category: str, brand_demand: Decimal) -> Decimal:
    category_liquidity = {
        "bags": 75,
        "shoes": 70,
        "outerwear": 55,
        "denim": 60,
        "knitwear": 50,
        "accessories": 65,
        "jewelry": 45,
        "eyewear": 50,
    }
    base = category_liquidity.get(category, 50)
    adjusted = base * 0.6 + float(brand_demand) * 0.4
    return clamp_score(adjusted)


def compute_risk_score(
    brand: Brand,
    match: Match,
    listing: Listing,
    liquidity_score: Decimal,
) -> Decimal:
    counterfeit = float(brand.counterfeit_risk)
    match_risk = 100.0 - float(match.match_confidence)
    condition_risk = {"new": 5, "excellent": 10, "good": 25, "fair": 45}.get(listing.condition, 30)
    liquidity_risk = 100.0 - float(liquidity_score)
    desc_risk = 30.0 if not listing.description or len(listing.description) < 30 else 10.0

    risk = (
        counterfeit * 0.30
        + match_risk * 0.25
        + condition_risk * 0.20
        + liquidity_risk * 0.15
        + desc_risk * 0.10
    )
    return clamp_score(risk)


def compute_purchase_cost(
    listing: Listing,
    marketplace: Marketplace,
) -> tuple[Decimal, dict]:
    price = listing.price_eur
    shipping = marketplace.default_shipping_eur
    buyer_fee = price * marketplace.buyer_fee_pct + Decimal("0.70")
    fx_cost = price * Decimal("0.005") if listing.currency_original != "EUR" else Decimal("0")
    import_cost = (price + shipping) * Decimal("0.15")

    total = price + shipping + buyer_fee + fx_cost + import_cost
    breakdown = {
        "item_price_eur": float(price),
        "shipping_eur": float(shipping),
        "buyer_fee_eur": float(buyer_fee.quantize(Decimal("0.01"))),
        "fx_cost_eur": float(fx_cost.quantize(Decimal("0.01"))),
        "import_cost_eur": float(import_cost.quantize(Decimal("0.01"))),
        "total_eur": float(total.quantize(Decimal("0.01"))),
    }
    return total.quantize(Decimal("0.01")), breakdown


def compute_expected_sale(
    target: Listing,
    marketplace: Marketplace,
) -> tuple[Decimal, Decimal]:
    condition_mult = {
        "new": Decimal("1.00"),
        "excellent": Decimal("1.00"),
        "good": Decimal("0.92"),
        "fair": Decimal("0.85"),
    }.get(target.condition, Decimal("0.92"))

    gross = (target.price_eur * condition_mult).quantize(Decimal("0.01"))
    seller_fee = (gross * marketplace.seller_fee_pct).quantize(Decimal("0.01"))
    net = gross - seller_fee
    return gross, net.quantize(Decimal("0.01"))


def compute_opportunity(
    purchase_listing: Listing,
    sale_listing: Listing,
    purchase_marketplace: Marketplace,
    sale_marketplace: Marketplace,
    brand: Brand,
    match: Match,
) -> dict:
    purchase_cost, cost_breakdown = compute_purchase_cost(purchase_listing, purchase_marketplace)
    expected_gross, expected_net = compute_expected_sale(sale_listing, sale_marketplace)

    gross_profit = (expected_gross - purchase_cost).quantize(Decimal("0.01"))
    net_profit = (expected_net - purchase_cost).quantize(Decimal("0.01"))
    roi = (gross_profit / purchase_cost).quantize(Decimal("0.0001")) if purchase_cost > 0 else Decimal("0")

    roi_score = compute_roi_score(roi)
    demand_score = Decimal(str(brand.demand_score)).quantize(Decimal("0.01"))
    liquidity_score = compute_liquidity_score(purchase_listing.category, demand_score)
    price_gap_score = compute_price_gap_score(gross_profit, purchase_cost)
    risk_score = compute_risk_score(brand, match, purchase_listing, liquidity_score)

    w = SCORING_WEIGHTS
    opportunity_score = clamp_score(
        float(roi_score) * w["roi"]
        + float(demand_score) * w["demand"]
        + float(liquidity_score) * w["liquidity"]
        + float(price_gap_score) * w["price_gap"]
        - float(risk_score) * w["risk"]
    )

    recommendation = "SKIP"
    if float(opportunity_score) >= 75 and float(roi) >= 0.20 and float(net_profit) >= 50:
        recommendation = "BUY"
    elif float(opportunity_score) >= 50:
        recommendation = "WATCH"

    return {
        "purchase_cost_eur": purchase_cost,
        "expected_sale_price_eur": expected_gross,
        "expected_sale_price_rub": sale_listing.price_rub,
        "gross_profit_eur": gross_profit,
        "net_profit_eur": net_profit,
        "roi": roi,
        "roi_score": roi_score,
        "demand_score": demand_score,
        "liquidity_score": liquidity_score,
        "price_gap_score": price_gap_score,
        "risk_score": risk_score,
        "opportunity_score": opportunity_score,
        "recommendation": recommendation,
        "cost_breakdown": cost_breakdown,
    }
