"""End-to-end ingestion, matching, and scoring pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.constants import BRAND_ALIASES, CATEGORIES, PRIORITY_BRANDS
from app.models import Brand, Listing, Marketplace, Match, Opportunity, PriceHistory
from app.scrapers.oskelly import OskellyAdapter
from app.scrapers.vinted import VintedAdapter
from app.services.currency import currency_service
from app.services.matching import compute_match_confidence, passes_arbitrage_direction
from app.services.normalization import clean_title, normalize_brand, normalize_condition, normalize_size, slugify
from app.services.scoring import compute_opportunity
from app.services.search import listing_document, opportunity_document, sync_listings, sync_opportunities

logger = logging.getLogger(__name__)

SCRAPE_CATEGORIES = ["bags", "shoes", "outerwear", "denim", "knitwear", "accessories"]


async def ensure_marketplaces(db) -> dict[str, Marketplace]:
    result = await db.execute(select(Marketplace))
    existing = {m.slug: m for m in result.scalars().all()}
    defaults = [
        {
            "slug": "vinted",
            "name": "Vinted",
            "base_currency": "EUR",
            "buyer_fee_pct": "0.05",
            "seller_fee_pct": "0.00",
            "default_shipping_eur": "10.00",
            "country_code": "EU",
        },
        {
            "slug": "oskelly",
            "name": "Oskelly",
            "base_currency": "RUB",
            "buyer_fee_pct": "0.00",
            "seller_fee_pct": "0.12",
            "default_shipping_eur": "0.00",
            "country_code": "RU",
        },
    ]
    for d in defaults:
        if d["slug"] not in existing:
            mp = Marketplace(**d)
            db.add(mp)
            existing[d["slug"]] = mp
    await db.flush()
    return existing


async def ensure_brands(db) -> dict[str, Brand]:
    result = await db.execute(select(Brand))
    by_slug = {b.slug: b for b in result.scalars().all()}

    demand_scores = {
        "Prada": 85, "Miu Miu": 82, "Maison Margiela": 78, "Balenciaga": 80,
        "Rick Owens": 72, "Diesel": 65, "Acne Studios": 68, "Chrome Hearts": 75,
        "Saint Laurent": 83, "Gucci": 84, "Bottega Veneta": 81, "Comme des Garçons": 70,
    }
    counterfeit = {
        "Chrome Hearts": 55, "Gucci": 50, "Balenciaga": 45, "Prada": 40,
    }

    for name in PRIORITY_BRANDS:
        s = slugify(name)
        if s not in by_slug:
            brand = Brand(
                canonical_name=name,
                slug=s,
                aliases=BRAND_ALIASES.get(name, []),
                demand_score=Decimal(str(demand_scores.get(name, 60))),
                counterfeit_risk=Decimal(str(counterfeit.get(name, 30))),
            )
            db.add(brand)
            by_slug[s] = brand
    await db.flush()
    return by_slug


async def _upsert_listing(
    db,
    *,
    mp: Marketplace,
    brand: Brand,
    raw,
    seen_keys: set[tuple],
) -> tuple[Listing | None, bool]:
    """Returns (listing, is_new)."""
    key = (mp.id, raw.external_id)
    if key in seen_keys:
        return None, False
    seen_keys.add(key)

    size_norm, size_sys = normalize_size(raw.size_raw, raw.category, raw.size_system)
    eur, rub = currency_service.convert(raw.price, raw.currency)
    now = datetime.now(UTC)

    result = await db.execute(
        select(Listing).where(Listing.marketplace_id == mp.id, Listing.external_id == raw.external_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        price_changed = existing.price_eur != eur
        existing.title = raw.title
        existing.normalized_title = clean_title(raw.title, brand.canonical_name)
        existing.category = raw.category
        existing.subcategory = raw.subcategory
        existing.size_raw = raw.size_raw
        existing.size_normalized = size_norm
        existing.size_system = size_sys
        existing.condition = normalize_condition(raw.condition)
        existing.price_original = raw.price
        existing.currency_original = raw.currency
        existing.price_eur = eur
        existing.price_rub = rub
        existing.image_urls = raw.image_urls
        existing.description = raw.description
        existing.is_sold = raw.is_sold
        existing.is_active = not raw.is_sold
        existing.scraped_at = now
        existing.listing_url = raw.listing_url
        existing.raw_data = {"source": mp.slug, "scraped_at": now.isoformat()}

        if price_changed:
            db.add(PriceHistory(listing_id=existing.id, price_eur=eur, price_rub=rub, recorded_at=now))
        return existing, False

    listing = Listing(
        marketplace_id=mp.id,
        brand_id=brand.id,
        external_id=raw.external_id,
        title=raw.title,
        normalized_title=clean_title(raw.title, brand.canonical_name),
        category=raw.category,
        subcategory=raw.subcategory,
        size_raw=raw.size_raw,
        size_normalized=size_norm,
        size_system=size_sys,
        condition=normalize_condition(raw.condition),
        price_original=raw.price,
        currency_original=raw.currency,
        price_eur=eur,
        price_rub=rub,
        seller_country=raw.seller_country,
        listing_url=raw.listing_url,
        image_urls=raw.image_urls,
        description=raw.description,
        is_sold=raw.is_sold,
        is_active=not raw.is_sold,
        listed_at=raw.listed_at,
        scraped_at=now,
        raw_data={"source": mp.slug, "scraped_at": now.isoformat()},
    )
    db.add(listing)
    await db.flush()
    db.add(PriceHistory(listing_id=listing.id, price_eur=eur, price_rub=rub, recorded_at=now))
    return listing, True


async def cleanup_stale_listings(db, marketplace_id, hours: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    result = await db.execute(
        update(Listing)
        .where(
            Listing.marketplace_id == marketplace_id,
            Listing.is_active.is_(True),
            Listing.scraped_at < cutoff,
        )
        .values(is_active=False)
        .returning(Listing.id)
    )
    return len(result.fetchall())


async def ingest_listings(db) -> dict:
    settings = get_settings()
    await currency_service.refresh_rates()
    marketplaces = await ensure_marketplaces(db)
    brands = await ensure_brands(db)

    adapters = []
    if settings.vinted_enabled:
        if settings.vinted_proxy_url:
            from app.scrapers.vinted_proxy import VintedProxyAdapter
            adapters.append(VintedProxyAdapter())
            logger.info("Using Vinted proxy adapter via %s", settings.vinted_proxy_url)
        else:
            adapters.append(VintedAdapter())
    if settings.oskelly_enabled:
        adapters.append(OskellyAdapter())

    created = 0
    updated = 0
    seen_keys: set[tuple] = set()
    meili_docs: list[dict] = []
    limit = settings.scraper_listings_per_query

    for adapter in adapters:
        mp = marketplaces[adapter.slug]
        for brand_name in PRIORITY_BRANDS:
            canonical, _ = normalize_brand(brand_name)
            brand = brands.get(slugify(canonical))
            if not brand:
                continue

            # Brand-wide fetch (category filter applied post-parse)
            raw_listings = await adapter.fetch_listings(brand_name, "all", limit=limit)
            for raw in raw_listings:
                listing, is_new = await _upsert_listing(
                    db, mp=mp, brand=brand, raw=raw, seen_keys=seen_keys
                )
                if not listing:
                    continue
                if is_new:
                    created += 1
                else:
                    updated += 1
                meili_docs.append(listing_document(listing, brand.slug, mp.slug))

        stale = await cleanup_stale_listings(db, mp.id, settings.scraper_stale_hours)
        logger.info("Deactivated %s stale %s listings", stale, adapter.slug)

    await db.flush()
    await sync_listings(meili_docs)
    return {"created": created, "updated": updated, "indexed": len(meili_docs)}


async def run_matching(db) -> int:
    settings = get_settings()
    marketplaces = await ensure_marketplaces(db)
    vinted_id = marketplaces["vinted"].id
    oskelly_id = marketplaces["oskelly"].id

    vinted_result = await db.execute(
        select(Listing)
        .where(Listing.marketplace_id == vinted_id, Listing.is_active.is_(True))
        .options(selectinload(Listing.brand))
    )
    oskelly_result = await db.execute(
        select(Listing)
        .where(Listing.marketplace_id == oskelly_id, Listing.is_active.is_(True))
        .options(selectinload(Listing.brand))
    )
    vinted_listings = list(vinted_result.scalars().all())
    oskelly_listings = list(oskelly_result.scalars().all())

    created = 0
    for source in vinted_listings:
        best_target = None
        best_scores = None
        best_confidence = Decimal("0")

        for target in oskelly_listings:
            if source.brand_id != target.brand_id:
                continue
            if source.category != target.category:
                continue
            # Subcategory = canonical model name (e.g. "Jodie Bag", "Triple S").
            # If both sides have a subcategory it MUST be the same model.
            # This is the primary guard against apples-vs-oranges matches.
            if source.subcategory and target.subcategory:
                if source.subcategory.lower() != target.subcategory.lower():
                    continue
            if not passes_arbitrage_direction(source.price_eur, target.price_eur):
                continue

            scores = compute_match_confidence(
                brand_a=source.brand.canonical_name,
                brand_b=target.brand.canonical_name,
                aliases_a=source.brand.aliases,
                title_a=source.normalized_title,
                title_b=target.normalized_title,
                category_a=source.category,
                subcategory_a=source.subcategory,
                category_b=target.category,
                subcategory_b=target.subcategory,
                size_a=source.size_normalized,
                size_b=target.size_normalized,
                has_images=bool(source.image_urls and target.image_urls),
            )
            if scores["match_confidence"] > best_confidence:
                best_confidence = scores["match_confidence"]
                best_target = target
                best_scores = scores

        if best_target and best_scores and float(best_confidence) >= settings.match_confidence_threshold:
            existing = await db.execute(
                select(Match).where(
                    Match.source_listing_id == source.id,
                    Match.target_listing_id == best_target.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Remove weaker matches for same source so only the best match persists
            await db.execute(
                delete(Match)
                .where(Match.source_listing_id == source.id)
                .where(Match.match_confidence < best_confidence)
            )

            match = Match(
                source_listing_id=source.id,
                target_listing_id=best_target.id,
                **best_scores,
            )
            db.add(match)
            created += 1

    await db.flush()
    return created


async def run_scoring(db) -> dict:
    marketplaces = await ensure_marketplaces(db)
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.source_listing).selectinload(Listing.brand),
            selectinload(Match.source_listing).selectinload(Listing.marketplace),
            selectinload(Match.target_listing).selectinload(Listing.marketplace),
            selectinload(Match.opportunity),
        )
    )
    matches = result.scalars().all()
    created = 0
    updated = 0
    meili_docs: list[dict] = []

    for match in matches:
        source = match.source_listing
        target = match.target_listing
        if not source.is_active or not target.is_active:
            continue

        scores = compute_opportunity(
            purchase_listing=source,
            sale_listing=target,
            purchase_marketplace=marketplaces["vinted"],
            sale_marketplace=marketplaces["oskelly"],
            brand=source.brand,
            match=match,
        )

        if match.opportunity:
            opp = match.opportunity
            for field, value in scores.items():
                setattr(opp, field, value)
            opp.computed_at = datetime.now(UTC)
            updated += 1
        else:
            opp = Opportunity(
                match_id=match.id,
                purchase_listing_id=source.id,
                sale_listing_id=target.id,
                **scores,
            )
            db.add(opp)
            await db.flush()
            created += 1

        meili_docs.append(
            opportunity_document(opp)
            if opp.purchase_listing
            else {
                "id": str(opp.id),
                "opportunity_score": float(opp.opportunity_score),
                "recommendation": opp.recommendation,
                "roi": float(opp.roi),
                "gross_profit_eur": float(opp.gross_profit_eur),
                "brand_slug": source.brand.slug,
                "category": source.category,
                "risk_score": float(opp.risk_score),
                "title": source.title,
            }
        )

    await db.flush()
    await sync_opportunities(meili_docs)
    return {"created": created, "updated": updated, "indexed": len(meili_docs)}


async def run_full_pipeline(db) -> dict:
    ingest_stats = await ingest_listings(db)
    matched = await run_matching(db)
    scoring_stats = await run_scoring(db)
    return {
        "listings_created": ingest_stats["created"],
        "listings_updated": ingest_stats["updated"],
        "listings_indexed": ingest_stats["indexed"],
        "matches_created": matched,
        "opportunities_created": scoring_stats["created"],
        "opportunities_updated": scoring_stats["updated"],
    }
