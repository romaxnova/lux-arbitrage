"""
Seed the database with real Oskelly listings + Vinted search counterparts.

Run as: python -m app.scripts.demo_seed
Or trigger via: POST /api/v1/admin/seed-demo

Oskelly listings are scraped live (real URLs + images).
For each Oskelly listing a paired "virtual" Vinted entry is created
with a realistic buy-price estimate (45 % of Oskelly EUR price) and a
Vinted search URL so the user can immediately find comparable items.

Only pairs with gross profit > MIN_GROSS_PROFIT_EUR are kept.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import quote_plus

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import Brand, Listing, Marketplace, PriceHistory
from app.scrapers.oskelly import OskellyAdapter
from app.services.currency import currency_service
from app.services.normalization import clean_title, normalize_size, slugify
from app.services.pipeline import ensure_brands, ensure_marketplaces, run_matching, run_scoring

logger = logging.getLogger(__name__)

MIN_OSKELLY_EUR = 550          # only Oskelly items above this EUR value
VINTED_PRICE_RATIO = Decimal("0.42")   # estimated Vinted buy = 42 % of Oskelly price
MIN_GROSS_PROFIT_EUR = 250     # discard pairs where expected gross profit < this


# Fallback high-value pairs used when Oskelly scrape yields too few results.
# Each tuple: (brand, category, oskelly_eur, vinted_search_keywords, oskelly_title, oskelly_image_url)
FALLBACK_PAIRS: list[tuple] = [
    ("Prada", "bags", 912,
     "Prada Re-Edition 2000 nylon bag",
     "PRADA Сумка Re-Edition нейлон",
     "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400"),
    ("Prada", "bags", 853,
     "Prada galleria saffiano leather bag",
     "PRADA Сумка Galleria саффиано",
     "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400"),
    ("Prada", "shoes", 710,
     "Prada monolith leather boots",
     "PRADA Ботинки Monolith кожа",
     "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400"),
    ("Miu Miu", "bags", 985,
     "Miu Miu wander nappa leather bag",
     "MIU MIU Сумка Wander nappa",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
    ("Miu Miu", "bags", 670,
     "Miu Miu crystal embellished mini bag",
     "MIU MIU Сумка мини кристаллы",
     "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400"),
    ("Miu Miu", "shoes", 780,
     "Miu Miu ballet flats metallic silver",
     "MIU MIU Балетки металлик серебро",
     "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400"),
    ("Balenciaga", "bags", 1050,
     "Balenciaga Le Cagole XS shoulder bag",
     "BALENCIAGA Сумка Le Cagole XS",
     "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400"),
    ("Balenciaga", "shoes", 820,
     "Balenciaga Triple S sneakers",
     "BALENCIAGA Кроссовки Triple S",
     "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
    ("Saint Laurent", "bags", 1200,
     "Saint Laurent Loulou medium quilted leather bag",
     "SAINT LAURENT Сумка Loulou стеганая кожа",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
    ("Saint Laurent", "bags", 870,
     "Saint Laurent Sunset medium bag",
     "SAINT LAURENT Сумка Sunset",
     "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400"),
    ("Gucci", "bags", 1080,
     "Gucci Horsebit 1955 shoulder bag GG Supreme",
     "GUCCI Сумка Horsebit 1955 GG Supreme",
     "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400"),
    ("Gucci", "bags", 780,
     "Gucci Marmont mini bag matelasse leather",
     "GUCCI Сумка Marmont мини стеганая",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
    ("Bottega Veneta", "bags", 1350,
     "Bottega Veneta Intrecciato pouch black",
     "BOTTEGA VENETA Клатч плетеная кожа",
     "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400"),
    ("Bottega Veneta", "bags", 980,
     "Bottega Veneta Cassette padded intrecciato",
     "BOTTEGA VENETA Сумка Cassette плетение",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
    ("Maison Margiela", "shoes", 760,
     "Maison Margiela Tabi boots black",
     "MAISON MARGIELA Ботинки Tabi черные",
     "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400"),
    ("Maison Margiela", "bags", 820,
     "Maison Margiela Glam Slam medium bag",
     "MAISON MARGIELA Сумка Glam Slam",
     "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400"),
    ("Rick Owens", "outerwear", 950,
     "Rick Owens leather biker jacket",
     "RICK OWENS Байкерская куртка кожа",
     "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400"),
    ("Rick Owens", "shoes", 870,
     "Rick Owens Ramones sneakers",
     "RICK OWENS Кроссовки Ramones",
     "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
    ("Chrome Hearts", "knitwear", 780,
     "Chrome Hearts cross logo hoodie",
     "CHROME HEARTS Худи логотип крест",
     "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=400"),
    ("Acne Studios", "bags", 620,
     "Acne Studios Musubi micro bag",
     "ACNE STUDIOS Сумка Musubi мини",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
]

VINTED_CATEGORY_KEYWORDS: dict[str, str] = {
    "bags": "bag sac",
    "shoes": "shoes sneakers",
    "outerwear": "jacket coat",
    "knitwear": "sweater hoodie",
    "denim": "jeans denim",
    "accessories": "accessory",
}


def vinted_search_url(brand: str, category: str) -> str:
    keywords = f"{brand} {VINTED_CATEGORY_KEYWORDS.get(category, category)}"
    return f"https://www.vinted.fr/catalog?search_text={quote_plus(keywords)}"


async def _upsert_demo_listing(
    db,
    *,
    mp: Marketplace,
    brand: Brand,
    ext_id: str,
    title: str,
    category: str,
    size_raw: str | None,
    price_eur: Decimal,
    currency: str,
    listing_url: str,
    image_urls: list[str],
    description: str,
) -> Listing | None:
    existing = (
        await db.execute(
            select(Listing).where(Listing.marketplace_id == mp.id, Listing.external_id == ext_id)
        )
    ).scalar_one_or_none()
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
        subcategory=None,
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


def _estimate_profit(oskelly_eur: float) -> float:
    """Rough gross profit estimate: oskelly_eur - purchase_cost_at_42pct_ratio."""
    vinted_price = oskelly_eur * 0.42
    shipping = 10
    buyer_fee = vinted_price * 0.05 + 0.70
    import_cost = (vinted_price + shipping) * 0.15
    purchase_cost = vinted_price + shipping + buyer_fee + import_cost
    return oskelly_eur - purchase_cost


async def _seed_from_oskelly(db, brands: dict, marketplaces: dict) -> tuple[int, int]:
    """Scrape real Oskelly data and pair with Vinted search counterparts."""
    oskelly_mp = marketplaces["oskelly"]
    vinted_mp = marketplaces["vinted"]
    adapter = OskellyAdapter()

    vinted_created = 0
    oskelly_created = 0

    from app.core.constants import PRIORITY_BRANDS

    for brand_name in PRIORITY_BRANDS:
        brand_slug = slugify(brand_name)
        brand = brands.get(brand_slug)
        if not brand:
            continue

        try:
            raw_listings = await adapter.fetch_listings(brand_name, "all", limit=20)
        except Exception as exc:
            logger.warning("Oskelly scrape failed for %s: %s", brand_name, exc)
            continue

        for raw in raw_listings:
            # Filter to high-value items only
            if float(raw.price) < MIN_OSKELLY_EUR * float(currency_service.get_rate("RUB")):
                continue  # too cheap in RUB terms; skip

            eur_rate = currency_service.get_rate("RUB")
            oskelly_eur = float(raw.price / eur_rate) if raw.currency == "RUB" else float(raw.price)

            if oskelly_eur < MIN_OSKELLY_EUR:
                continue

            expected_profit = _estimate_profit(oskelly_eur)
            if expected_profit < MIN_GROSS_PROFIT_EUR:
                continue

            # Oskelly listing (real)
            o_ext_id = f"real_oskelly_{raw.external_id}"
            ol = await _upsert_demo_listing(
                db,
                mp=oskelly_mp,
                brand=brand,
                ext_id=o_ext_id,
                title=raw.title,
                category=raw.category,
                size_raw=raw.size_raw,
                price_eur=Decimal(str(raw.price)),
                currency=raw.currency,
                listing_url=raw.listing_url,
                image_urls=raw.image_urls,
                description=raw.description or raw.title,
            )
            if ol:
                oskelly_created += 1

            # Vinted virtual listing (search URL)
            vinted_eur = Decimal(str(round(oskelly_eur * float(VINTED_PRICE_RATIO), 2)))
            v_ext_id = f"vinted_for_{raw.external_id}"
            vl = await _upsert_demo_listing(
                db,
                mp=vinted_mp,
                brand=brand,
                ext_id=v_ext_id,
                title=f"{brand_name} {raw.category} (search Vinted)",
                category=raw.category,
                size_raw=raw.size_raw,
                price_eur=vinted_eur,
                currency="EUR",
                listing_url=vinted_search_url(brand_name, raw.category),
                image_urls=[],
                description=f"Find {brand_name} {raw.category} items on Vinted",
            )
            if vl:
                vinted_created += 1

    return vinted_created, oskelly_created


async def _seed_fallback(db, brands: dict, marketplaces: dict) -> tuple[int, int]:
    """Seed from hardcoded high-value pairs (fallback when scrape yields few results)."""
    oskelly_mp = marketplaces["oskelly"]
    vinted_mp = marketplaces["vinted"]
    vinted_created = 0
    oskelly_created = 0

    for i, (brand_name, category, oskelly_eur_int, v_keywords, o_title, o_image) in enumerate(FALLBACK_PAIRS):
        brand_slug = slugify(brand_name)
        brand = brands.get(brand_slug)
        if not brand:
            continue

        oskelly_eur = Decimal(str(oskelly_eur_int))
        vinted_eur = (oskelly_eur * VINTED_PRICE_RATIO).quantize(Decimal("0.01"))

        # Oskelly listing
        o_ext_id = f"fb_oskelly_{i:04d}"
        ol = await _upsert_demo_listing(
            db,
            mp=oskelly_mp,
            brand=brand,
            ext_id=o_ext_id,
            title=o_title,
            category=category,
            size_raw=None,
            price_eur=oskelly_eur,
            currency="EUR",
            listing_url=f"https://oskelly.ru/catalog?search={quote_plus(brand_name)}",
            image_urls=[o_image],
            description=o_title,
        )
        if ol:
            oskelly_created += 1

        # Vinted virtual listing
        v_ext_id = f"fb_vinted_{i:04d}"
        vl = await _upsert_demo_listing(
            db,
            mp=vinted_mp,
            brand=brand,
            ext_id=v_ext_id,
            title=f"{brand_name} {v_keywords}",
            category=category,
            size_raw=None,
            price_eur=vinted_eur,
            currency="EUR",
            listing_url=vinted_search_url(brand_name, category),
            image_urls=[],
            description=f"Find on Vinted: {v_keywords}",
        )
        if vl:
            vinted_created += 1

    return vinted_created, oskelly_created


async def run_demo_seed(db) -> dict:
    """Populate DB with demo listings, run matching and scoring. Idempotent."""
    await currency_service.refresh_rates()
    marketplaces = await ensure_marketplaces(db)
    brands = await ensure_brands(db)

    # Try live Oskelly scrape first
    logger.info("Demo seed: scraping Oskelly for high-value listings...")
    v1, o1 = await _seed_from_oskelly(db, brands, marketplaces)
    logger.info("Oskelly scrape: %s vinted + %s oskelly listings", v1, o1)

    # Always supplement with fallback pairs so we have solid coverage
    v2, o2 = await _seed_fallback(db, brands, marketplaces)
    logger.info("Fallback pairs: %s vinted + %s oskelly listings", v2, o2)

    await db.flush()

    # Re-run matching and scoring
    matches = await run_matching(db)
    scoring = await run_scoring(db)

    return {
        "oskelly_real_listings": o1,
        "vinted_virtual_listings": v1,
        "fallback_pairs": o2,
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
