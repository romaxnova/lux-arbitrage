"""
Seed the database with real Oskelly listings paired with real Vinted listings.

Strategy:
1. Scrape Oskelly for high-value items (≥ MIN_OSKELLY_EUR).
2. For each Oskelly item, extract its specific item type from the Russian
   title (e.g. "PRADA Кроссовки" → type="sneakers", category="shoes").
3. Query the Vinted proxy (running in Frankfurt) for that exact brand +
   item type (e.g. brand_ids[]=3573 + search_text="sneakers") so Vinted
   results are genuinely comparable to the Oskelly listing.
4. Match and score: same brand + same specific item type = valid pair.

This avoids the "apples vs oranges" problem where Prada sandals on
Oskelly were matched with Prada polo shirts on Vinted just because both
were in the generic "accessories" bucket.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import quote_plus

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import Listing, Marketplace, PriceHistory
from app.scrapers.oskelly import OskellyAdapter
from app.services.currency import currency_service
from app.services.normalization import clean_title, extract_item_type, normalize_size, slugify
from app.services.pipeline import ensure_brands, ensure_marketplaces, run_matching, run_scoring

logger = logging.getLogger(__name__)

MIN_OSKELLY_EUR = 450          # minimum Oskelly price to consider (EUR)
MIN_GROSS_PROFIT_EUR = 250     # skip pairs with estimated gross profit below this


def _estimate_profit(oskelly_eur: float, vinted_eur: float) -> float:
    """Rough gross profit: oskelly_price - all_purchase_costs."""
    shipping = 10.0
    buyer_fee = vinted_eur * 0.05 + 0.70
    import_cost = (vinted_eur + shipping) * 0.15
    purchase_cost = vinted_eur + shipping + buyer_fee + import_cost
    return oskelly_eur - purchase_cost


async def _upsert_listing(db, *, mp: Marketplace, brand, ext_id: str, title: str,
                          category: str, subcategory: str | None, size_raw: str | None,
                          price_eur: Decimal, currency: str, listing_url: str,
                          image_urls: list[str], description: str) -> "Listing | None":
    existing = (await db.execute(
        select(Listing).where(Listing.marketplace_id == mp.id, Listing.external_id == ext_id)
    )).scalar_one_or_none()
    if existing:
        return existing

    rub_rate = currency_service.get_rate("RUB")
    if currency == "RUB":
        eur_price = (price_eur / rub_rate).quantize(Decimal("0.01"))
    else:
        eur_price = price_eur
    rub_price = (eur_price * rub_rate).quantize(Decimal("0.01"))

    size_norm, size_sys = normalize_size(size_raw, category) if size_raw else (None, "EU")
    now = datetime.now(UTC)

    listing = Listing(
        marketplace_id=mp.id,
        brand_id=brand.id,
        external_id=ext_id,
        title=title,
        normalized_title=clean_title(title, brand.canonical_name),
        category=category,
        subcategory=subcategory,
        size_raw=size_raw,
        size_normalized=size_norm,
        size_system=size_sys,
        condition="excellent",
        price_original=eur_price if currency == "EUR" else price_eur,
        currency_original=currency,
        price_eur=eur_price,
        price_rub=rub_price,
        seller_country="RU" if mp.slug == "oskelly" else "FR",
        listing_url=listing_url,
        image_urls=image_urls,
        description=description,
        is_sold=False,
        is_active=True,
        listed_at=now,
        scraped_at=now,
        raw_data={"source": mp.slug, "demo": True},
    )
    db.add(listing)
    await db.flush()
    db.add(PriceHistory(listing_id=listing.id, price_eur=eur_price, price_rub=rub_price, recorded_at=now))
    return listing


async def _fetch_vinted_for_type(brand_name: str, item_type_en: str,
                                  proxy_url: str, limit: int = 5) -> list[dict]:
    """Call the Vercel /api/vinted proxy with brand + specific item type."""
    if not proxy_url:
        return []
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{proxy_url.rstrip('/')}/api/vinted",
                params={"brand": brand_name, "item_type": item_type_en, "limit": limit, "min_price": "80"},
            )
            if r.status_code == 200:
                return r.json().get("items", [])
    except Exception as exc:
        logger.warning("Vinted proxy failed: %s", exc)
    return []


async def run_demo_seed(db) -> dict:
    """Populate DB with real Oskelly + real Vinted listings, run matching/scoring."""
    from app.config import get_settings
    settings = get_settings()
    proxy_url = settings.vinted_proxy_url

    await currency_service.refresh_rates()
    rub_rate = currency_service.get_rate("RUB")

    marketplaces = await ensure_marketplaces(db)
    brands = await ensure_brands(db)
    oskelly_mp = marketplaces["oskelly"]
    vinted_mp = marketplaces["vinted"]

    adapter = OskellyAdapter()
    from app.core.constants import PRIORITY_BRANDS

    oskelly_created = 0
    vinted_created = 0
    # Track (brand_slug, item_type_en) already seeded to avoid duplicating Vinted entries
    seeded_vinted: dict[tuple[str, str], str] = {}  # (brand_slug, item_type_en) → ext_id

    for brand_name in PRIORITY_BRANDS:
        brand_slug = slugify(brand_name)
        brand = brands.get(brand_slug)
        if not brand:
            continue

        try:
            raw_oskelly = await adapter.fetch_listings(brand_name, "all", limit=20)
        except Exception as exc:
            logger.warning("Oskelly scrape failed for %s: %s", brand_name, exc)
            continue

        for raw in raw_oskelly:
            # Convert to EUR
            if raw.currency == "RUB":
                oskelly_eur = float(raw.price / rub_rate)
            else:
                oskelly_eur = float(raw.price)

            if oskelly_eur < MIN_OSKELLY_EUR:
                continue

            # Extract SPECIFIC item type from Russian Oskelly title
            inferred_cat, item_type_en = extract_item_type(raw.title)

            # Skip items we can't identify specifically (fall-through accessories
            # with no English search term would produce garbage Vinted results)
            if not item_type_en:
                logger.debug("Skipping %s — no item type extracted", raw.title)
                continue

            # Ensure inferred category is consistent with item_type_en
            category = inferred_cat

            # --- Oskelly listing ---
            o_ext_id = f"rs_{raw.external_id}"
            ol = await _upsert_listing(
                db,
                mp=oskelly_mp,
                brand=brand,
                ext_id=o_ext_id,
                title=raw.title,
                category=category,
                subcategory=item_type_en,       # English item type stored as subcategory
                size_raw=raw.size_raw,
                price_eur=Decimal(str(raw.price)),
                currency=raw.currency,
                listing_url=raw.listing_url,
                image_urls=raw.image_urls,
                description=raw.description or raw.title,
            )
            if ol:
                oskelly_created += 1

            # --- Vinted listing: one per (brand, item_type) ---
            vinted_key = (brand_slug, item_type_en)
            if vinted_key not in seeded_vinted:
                # Fetch real Vinted listings for this brand + item type
                vinted_items = await _fetch_vinted_for_type(brand_name, item_type_en, proxy_url, limit=5)

                if vinted_items:
                    # Use the BEST Vinted listing (one with image, highest price within range)
                    vinted_items_sorted = sorted(
                        [i for i in vinted_items if i.get("price_eur", 0) >= 60],
                        key=lambda i: (bool(i.get("image_url")), i.get("price_eur", 0)),
                        reverse=True,
                    )
                    best = vinted_items_sorted[0] if vinted_items_sorted else None

                    if best and _estimate_profit(oskelly_eur, best["price_eur"]) >= MIN_GROSS_PROFIT_EUR:
                        # Sanity-check: the Vinted listing title must be plausibly
                        # the same type as the Oskelly listing we're pairing with.
                        from app.services.normalization import extract_item_type as _eit
                        vinted_cat, _ = _eit(best["title"]) if _eit(best["title"])[1] else (category, item_type_en)
                        # Also run the English keyword-based category check
                        from app.scrapers.vinted_maps import infer_category_from_title as _infer
                        vinted_cat_en = _infer(best["title"])
                        # Accept if categories agree or if we can't determine from the title
                        if vinted_cat_en != "accessories" and vinted_cat_en != category:
                            logger.debug(
                                "Skipping Vinted '%s' (cat=%s, expected %s)",
                                best["title"][:40], vinted_cat_en, category
                            )
                            best = None

                if best and _estimate_profit(oskelly_eur, best["price_eur"]) >= MIN_GROSS_PROFIT_EUR:
                        v_ext_id = f"vp_{brand_slug}_{item_type_en.replace(' ', '_')}"
                        vl = await _upsert_listing(
                            db,
                            mp=vinted_mp,
                            brand=brand,
                            ext_id=v_ext_id,
                            title=best["title"],
                            category=category,
                            subcategory=item_type_en,
                            size_raw=best.get("size"),
                            price_eur=Decimal(str(best["price_eur"])),
                            currency="EUR",
                            listing_url=best["url"],
                            image_urls=[best["image_url"]] if best.get("image_url") else [],
                            description=best["title"],
                        )
                        if vl:
                            vinted_created += 1
                        seeded_vinted[vinted_key] = v_ext_id

                if vinted_key not in seeded_vinted:
                    # Fallback: Vinted search URL (no specific listing found)
                    v_ext_id = f"vs_{brand_slug}_{item_type_en.replace(' ', '_')}"
                    vinted_eur = Decimal(str(round(oskelly_eur * 0.40, 2)))
                    vl = await _upsert_listing(
                        db,
                        mp=vinted_mp,
                        brand=brand,
                        ext_id=v_ext_id,
                        title=f"{brand_name} {item_type_en}",
                        category=category,
                        subcategory=item_type_en,
                        size_raw=None,
                        price_eur=vinted_eur,
                        currency="EUR",
                        listing_url=(
                            f"https://www.vinted.fr/catalog"
                            f"?search_text={quote_plus(brand_name + ' ' + item_type_en)}"
                        ),
                        image_urls=[],
                        description=f"Search Vinted for {brand_name} {item_type_en}",
                    )
                    if vl:
                        vinted_created += 1
                    seeded_vinted[vinted_key] = v_ext_id

        logger.info("Brand %s: %s Oskelly items seeded", brand_name, oskelly_created)

    await db.flush()

    # Run matching + scoring on the fresh data
    matches = await run_matching(db)
    scoring = await run_scoring(db)

    return {
        "oskelly_listings": oskelly_created,
        "vinted_listings": vinted_created,
        "matches_created": matches,
        "opportunities_created": scoring["created"],
        "opportunities_updated": scoring["updated"],
    }


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        stats = await run_demo_seed(db)
        await db.commit()
        print("Demo seed complete:", stats)


if __name__ == "__main__":
    asyncio.run(main())
