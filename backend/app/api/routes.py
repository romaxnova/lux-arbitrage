from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
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

    # Fetch all candidates (with extra headroom) and deduplicate by sale listing
    # so the same Oskelly product is shown at most once (the best match wins).
    fetch_limit = min(page_size * 10, 500)
    result = await db.execute(query.limit(fetch_limit))
    all_opps = result.scalars().unique().all()

    seen_sale_ids: set = set()
    unique_opps = []
    for o in all_opps:
        if o.sale_listing_id not in seen_sale_ids:
            seen_sale_ids.add(o.sale_listing_id)
            unique_opps.append(o)

    total = len(unique_opps)
    start = (page - 1) * page_size
    items = [opportunity_out(o) for o in unique_opps[start : start + page_size]]
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
    # Deduplicate by sale listing — each Oskelly item shown at most once
    seen: set = set()
    deduped = []
    for o in result.scalars().all():
        if o.sale_listing_id not in seen:
            seen.add(o.sale_listing_id)
            deduped.append(o)
    return [opportunity_out(o) for o in deduped]


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


@router.post("/opportunities/{opportunity_id}/post-to-oskelly")
async def post_to_oskelly(
    opportunity_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    publish: bool = False,
):
    """Generate an adapted Russian Oskelly listing for an opportunity.

    The item we'd buy on Vinted is re-listed for sale on Oskelly. We build an
    original Russian title + description (never a copy of the source text) and,
    when ?publish=true AND posting is enabled, hand it to the Oskelly publisher.
    Otherwise we return the preview so the operator can review before posting.
    """
    from app.services.normalization import resolve_semantics
    from app.services.oskelly_publisher import OskellyPublisher, build_russian_listing, listing_to_dict

    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.purchase_listing).selectinload(Listing.brand),
            selectinload(Opportunity.sale_listing).selectinload(Listing.brand),
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    source = opp.purchase_listing      # the item we buy (Vinted) and re-sell
    comp = opp.sale_listing            # the Oskelly comparable that sets price
    brand_name = source.brand.canonical_name

    model, item_type = resolve_semantics(
        brand=brand_name,
        category=source.category,
        subcategory=source.subcategory,
        title=source.title or source.normalized_title,
        description=source.description,
    )

    listing = build_russian_listing(
        brand=brand_name,
        model=model,
        item_type=item_type,
        category=source.category,
        condition=source.condition,
        size=source.size_normalized or source.size_raw,
        price_rub=float(comp.price_rub or 0),
        images=(source.image_urls or comp.image_urls or []),
    )

    publisher = OskellyPublisher()
    if publish:
        publish_result = await publisher.publish(listing)
    else:
        publish_result = {
            "status": "preview",
            "message": "Предпросмотр карточки. Отправьте publish=true для публикации.",
            "publish_enabled": publisher.enabled,
            "credentials_configured": publisher.is_configured(),
        }

    return {"listing": listing_to_dict(listing), "result": publish_result}


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


@router.get("/market/category-analysis")
async def category_analysis(db: Annotated[AsyncSession, Depends(get_db)]):
    """Average prices per brand+category on each marketplace, ranked by spread (high to low)."""
    from sqlalchemy import and_

    rows = await db.execute(
        select(
            Brand.canonical_name.label("brand"),
            Brand.slug.label("brand_slug"),
            Listing.category,
            Marketplace.slug.label("marketplace"),
            func.avg(Listing.price_eur).label("avg_price"),
            func.count(Listing.id).label("listing_count"),
        )
        .join(Listing.brand)
        .join(Listing.marketplace)
        .where(Listing.is_active.is_(True))
        .group_by(Brand.canonical_name, Brand.slug, Listing.category, Marketplace.slug)
        .order_by(Brand.canonical_name, Listing.category)
    )
    raw = rows.all()

    # Pivot: {(brand, category): {marketplace: avg_price}}
    pivot: dict[tuple[str, str, str], dict] = {}
    for row in raw:
        key = (row.brand, row.brand_slug, row.category)
        if key not in pivot:
            pivot[key] = {"brand": row.brand, "brand_slug": row.brand_slug, "category": row.category}
        pivot[key][f"{row.marketplace}_avg_eur"] = round(float(row.avg_price or 0), 2)
        pivot[key][f"{row.marketplace}_count"] = row.listing_count

    # Build result with spread = oskelly_avg - vinted_avg
    result = []
    for entry in pivot.values():
        v = entry.get("vinted_avg_eur", 0)
        o = entry.get("oskelly_avg_eur", 0)
        if v > 0 and o > 0:
            entry["spread_eur"] = round(o - v, 2)
            entry["spread_pct"] = round((o - v) / v * 100, 1) if v > 0 else 0
            result.append(entry)

    result.sort(key=lambda x: x.get("spread_eur", 0), reverse=True)
    return result


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


@router.post("/admin/seed-demo")
async def seed_demo(background_tasks: BackgroundTasks, db: Annotated[AsyncSession, Depends(get_db)]):
    """Populate the database with realistic demo listings and run matching/scoring.

    Runs as a background task to avoid request timeouts on slow hosts.
    Safe to call multiple times — skips listings that already exist.
    """
    from app.scripts.demo_seed import run_demo_seed

    async def _run():
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as bg_db:
            stats = await run_demo_seed(bg_db)
            await bg_db.commit()
            import logging
            logging.getLogger(__name__).info("seed-demo complete: %s", stats)

    background_tasks.add_task(_run)
    return {"status": "seeding_started", "message": "Demo seed running in background — check /api/v1/market/stats in ~60s"}


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
