from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import authenticate_user, create_access_token, hash_password
from app.database import get_db
from app.dependencies import require_user
from app.models import Alert, Brand, Listing, Marketplace, Match, Opportunity, User, Watchlist
from app.schemas.common import (
    AlertCreate,
    AlertOut,
    BrandAnalytics,
    BrandBrief,
    ListingBrief,
    OpportunityDetail,
    OpportunityOut,
    PaginatedResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    WatchlistCreate,
    WatchlistOut,
)

router = APIRouter()


def listing_brief(listing: Listing, marketplace_slug: str) -> ListingBrief:
    return ListingBrief(
        id=listing.id,
        title=listing.title,
        price_eur=float(listing.price_eur),
        marketplace=marketplace_slug,
        url=listing.listing_url,
        image_urls=listing.image_urls or [],
        condition=listing.condition,
        size_normalized=listing.size_normalized,
        category=listing.category,
    )


def opportunity_out(opp: Opportunity) -> OpportunityOut:
    purchase = opp.purchase_listing
    sale = opp.sale_listing
    return OpportunityOut(
        id=opp.id,
        opportunity_score=float(opp.opportunity_score),
        recommendation=opp.recommendation,
        roi=float(opp.roi),
        gross_profit_eur=float(opp.gross_profit_eur),
        net_profit_eur=float(opp.net_profit_eur),
        demand_score=float(opp.demand_score),
        liquidity_score=float(opp.liquidity_score),
        risk_score=float(opp.risk_score),
        roi_score=float(opp.roi_score),
        price_gap_score=float(opp.price_gap_score),
        purchase_cost_eur=float(opp.purchase_cost_eur),
        expected_sale_price_eur=float(opp.expected_sale_price_eur),
        purchase_listing=listing_brief(purchase, purchase.marketplace.slug),
        sale_listing=listing_brief(sale, sale.marketplace.slug),
        brand=BrandBrief(
            name=purchase.brand.canonical_name,
            slug=purchase.brand.slug,
            tier=purchase.brand.tier,
        ),
    )


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(require_user)]):
    return user


@router.get("/opportunities", response_model=PaginatedResponse)
async def list_opportunities(
    db: Annotated[AsyncSession, Depends(get_db)],
    brand: str | None = None,
    category: str | None = None,
    size: str | None = None,
    country: str | None = None,
    min_profit: float | None = None,
    min_roi: float | None = None,
    min_demand: float | None = None,
    max_risk: float | None = None,
    recommendation: str | None = None,
    sort: str = Query(default="score"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = (
        select(Opportunity)
        .join(Opportunity.purchase_listing)
        .join(Listing.brand)
        .join(Listing.marketplace)
        .options(
            selectinload(Opportunity.purchase_listing).selectinload(Listing.brand),
            selectinload(Opportunity.purchase_listing).selectinload(Listing.marketplace),
            selectinload(Opportunity.sale_listing).selectinload(Listing.marketplace),
        )
    )

    if brand:
        query = query.where(Brand.slug == brand)
    if category:
        query = query.where(Listing.category == category)
    if size:
        query = query.where(Listing.size_normalized == size)
    if country:
        query = query.where(Listing.seller_country == country)
    if min_profit is not None:
        query = query.where(Opportunity.gross_profit_eur >= min_profit)
    if min_roi is not None:
        query = query.where(Opportunity.roi >= min_roi)
    if min_demand is not None:
        query = query.where(Opportunity.demand_score >= min_demand)
    if max_risk is not None:
        query = query.where(Opportunity.risk_score <= max_risk)
    if recommendation:
        query = query.where(Opportunity.recommendation == recommendation.upper())

    sort_map = {
        "score": Opportunity.opportunity_score.desc(),
        "roi": Opportunity.roi.desc(),
        "profit": Opportunity.gross_profit_eur.desc(),
        "demand": Opportunity.demand_score.desc(),
        "risk": Opportunity.risk_score.asc(),
    }
    query = query.order_by(sort_map.get(sort, Opportunity.opportunity_score.desc()))

    count_query = select(func.count(Opportunity.id))
    if brand:
        count_query = count_query.join(Opportunity.purchase_listing).join(Listing.brand).where(Brand.slug == brand)
    if category:
        if not brand:
            count_query = count_query.join(Opportunity.purchase_listing)
        count_query = count_query.where(Listing.category == category)
    if min_profit is not None:
        count_query = count_query.where(Opportunity.gross_profit_eur >= min_profit)
    if min_roi is not None:
        count_query = count_query.where(Opportunity.roi >= min_roi)
    if min_demand is not None:
        count_query = count_query.where(Opportunity.demand_score >= min_demand)
    if max_risk is not None:
        count_query = count_query.where(Opportunity.risk_score <= max_risk)
    if recommendation:
        count_query = count_query.where(Opportunity.recommendation == recommendation.upper())

    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = [opportunity_out(o) for o in result.scalars().unique().all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/opportunities/rankings/{ranking_type}", response_model=list[OpportunityOut])
async def rankings(ranking_type: str, db: Annotated[AsyncSession, Depends(get_db)], limit: int = 10):
    sort_map = {
        "top": Opportunity.opportunity_score.desc(),
        "undervalued": Opportunity.price_gap_score.desc(),
        "highest_roi": Opportunity.roi.desc(),
        "fastest_moving": Opportunity.liquidity_score.desc(),
        "highest_demand": Opportunity.demand_score.desc(),
        "lowest_risk": Opportunity.risk_score.asc(),
    }
    if ranking_type not in sort_map:
        raise HTTPException(status_code=404, detail="Unknown ranking type")

    query = (
        select(Opportunity)
        .options(
            selectinload(Opportunity.purchase_listing).selectinload(Listing.brand),
            selectinload(Opportunity.purchase_listing).selectinload(Listing.marketplace),
            selectinload(Opportunity.sale_listing).selectinload(Listing.marketplace),
        )
        .order_by(sort_map[ranking_type])
        .limit(limit)
    )
    if ranking_type == "lowest_risk":
        query = query.where(Opportunity.opportunity_score >= 50)

    result = await db.execute(query)
    return [opportunity_out(o) for o in result.scalars().all()]


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity(opportunity_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.match),
            selectinload(Opportunity.purchase_listing).selectinload(Listing.brand),
            selectinload(Opportunity.purchase_listing).selectinload(Listing.marketplace),
            selectinload(Opportunity.sale_listing).selectinload(Listing.marketplace),
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    base = opportunity_out(opp)
    return OpportunityDetail(
        **base.model_dump(),
        cost_breakdown=opp.cost_breakdown,
        match_confidence=float(opp.match.match_confidence),
        computed_at=opp.computed_at,
    )


@router.get("/brands", response_model=list[BrandBrief])
async def list_brands(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Brand).order_by(Brand.canonical_name))
    brands = result.scalars().all()
    return [BrandBrief(name=b.canonical_name, slug=b.slug, tier=b.tier) for b in brands]


@router.get("/brands/{slug}", response_model=BrandAnalytics)
async def brand_analytics(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    brand_result = await db.execute(select(Brand).where(Brand.slug == slug))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    vinted = await db.execute(
        select(func.avg(Listing.price_eur))
        .join(Marketplace)
        .where(Listing.brand_id == brand.id, Marketplace.slug == "vinted", Listing.is_active.is_(True))
    )
    oskelly = await db.execute(
        select(func.avg(Listing.price_eur))
        .join(Marketplace)
        .where(Listing.brand_id == brand.id, Marketplace.slug == "oskelly", Listing.is_active.is_(True))
    )
    avg_v = float(vinted.scalar() or 0)
    avg_o = float(oskelly.scalar() or 0)

    opp_count = await db.execute(
        select(func.count())
        .select_from(Opportunity)
        .join(Opportunity.purchase_listing)
        .where(Listing.brand_id == brand.id)
    )

    roi_result = await db.execute(
        select(func.avg(Opportunity.roi))
        .join(Opportunity.purchase_listing)
        .where(Listing.brand_id == brand.id)
    )

    return BrandAnalytics(
        brand=BrandBrief(name=brand.canonical_name, slug=brand.slug, tier=brand.tier),
        avg_vinted_price_eur=round(avg_v, 2),
        avg_oskelly_price_eur=round(avg_o, 2),
        median_spread_eur=round(max(0, avg_o - avg_v), 2),
        median_roi=round(float(roi_result.scalar() or 0), 4),
        demand_trend="rising" if float(brand.demand_score) > 60 else "stable",
        liquidity_trend="stable",
        top_categories=[{"category": "bags", "median_roi": 0.45, "opportunity_count": 5}],
        active_opportunities=int(opp_count.scalar() or 0),
    )


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(user: Annotated[User, Depends(require_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()))
    return list(result.scalars().all())


@router.post("/alerts", response_model=AlertOut, status_code=201)
async def create_alert(
    payload: AlertCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    alert = Alert(user_id=user.id, name=payload.name, rule_type=payload.rule_type, conditions=payload.conditions)
    db.add(alert)
    await db.flush()
    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)


@router.get("/watchlists", response_model=list[WatchlistOut])
async def list_watchlist(
    user: Annotated[User, Depends(require_user)], db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id).order_by(Watchlist.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/watchlists", response_model=WatchlistOut, status_code=201)
async def add_watchlist(
    payload: WatchlistCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    item = Watchlist(
        user_id=user.id,
        opportunity_id=payload.opportunity_id,
        listing_id=payload.listing_id,
        notes=payload.notes,
    )
    db.add(item)
    await db.flush()
    return item


@router.get("/market/exchange-rates")
async def exchange_rates():
    from app.services.currency import currency_service

    await currency_service.refresh_rates()
    return {k: float(v) for k, v in currency_service._rates.items()}


@router.get("/market/marketplaces")
async def marketplaces(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Marketplace).where(Marketplace.is_active.is_(True)))
    return [
        {
            "slug": m.slug,
            "name": m.name,
            "base_currency": m.base_currency,
            "buyer_fee_pct": float(m.buyer_fee_pct),
            "seller_fee_pct": float(m.seller_fee_pct),
        }
        for m in result.scalars().all()
    ]


@router.get("/market/stats")
async def market_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    listings = await db.execute(select(func.count()).select_from(Listing).where(Listing.is_active.is_(True)))
    opps = await db.execute(select(func.count()).select_from(Opportunity))
    matches = await db.execute(select(func.count()).select_from(Match))
    buy = await db.execute(select(func.count()).select_from(Opportunity).where(Opportunity.recommendation == "BUY"))
    return {
        "active_listings": listings.scalar() or 0,
        "opportunities": opps.scalar() or 0,
        "matches": matches.scalar() or 0,
        "buy_recommendations": buy.scalar() or 0,
    }


@router.post("/admin/scrape/trigger")
async def trigger_scrape(db: Annotated[AsyncSession, Depends(get_db)]):
    from app.services.pipeline import run_full_pipeline

    stats = await run_full_pipeline(db)
    return {"status": "completed", "stats": stats}


@router.post("/admin/matching/run")
async def trigger_matching(db: Annotated[AsyncSession, Depends(get_db)]):
    from app.services.pipeline import run_matching

    count = await run_matching(db)
    return {"matches_created": count}


@router.post("/admin/scoring/run")
async def trigger_scoring(db: Annotated[AsyncSession, Depends(get_db)]):
    from app.services.pipeline import run_scoring

    stats = await run_scoring(db)
    return stats
