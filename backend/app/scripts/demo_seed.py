"""
Seed the database with realistic demo listings for both Vinted and Oskelly.

Run as: python -m app.scripts.demo_seed
Or trigger via: POST /api/v1/admin/seed-demo

This bypasses live scrapers so the app works even when Vinted/Oskelly
block the server's IP. Prices and brands reflect real market dynamics.
"""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import Brand, Listing, Marketplace, Match, PriceHistory
from app.services.currency import currency_service
from app.services.matching import compute_match_confidence, passes_arbitrage_direction
from app.services.normalization import clean_title, normalize_size, slugify
from app.services.pipeline import ensure_brands, ensure_marketplaces
from app.services.scoring import compute_opportunity

RUB_RATE = Decimal("98.50")


def eur(amount: float) -> Decimal:
    return Decimal(str(round(amount, 2)))


def rub(amount: float) -> Decimal:
    return Decimal(str(round(amount, 2)))


def rub_to_eur(amount_rub: float) -> Decimal:
    return (Decimal(str(amount_rub)) / RUB_RATE).quantize(Decimal("0.01"))


# (brand_name, category, vinted_eur_price, oskelly_rub_price, vinted_title, oskelly_title, size)
DEMO_LISTINGS: list[tuple] = [
    # Prada bags — strong arbitrage
    ("Prada", "bags", 320, 62000, "Prada Re-Edition 2000 nylon bag black", "PRADA Сумка Re-Edition 2000 нейлон", None),
    ("Prada", "bags", 280, 55000, "Prada galleria leather bag saffiano", "PRADA Сумка Galleria кожа саффиано", None),
    ("Prada", "bags", 190, 41000, "Prada cahier bag metallic gold", "PRADA Сумка Cahier металлик золото", None),
    ("Prada", "bags", 450, 89000, "Prada cleo brushed leather shoulder bag", "PRADA Сумка Cleo кожа", None),
    ("Prada", "shoes", 240, 48000, "Prada monolith leather boots black 38", "PRADA Ботинки Monolith кожа черные", "38"),
    ("Prada", "shoes", 180, 36000, "Prada block heel pumps satin 37", "PRADA Туфли каблук атлас", "37"),
    ("Prada", "accessories", 95, 22000, "Prada cardholder saffiano leather", "PRADA Кардхолдер саффиано", None),

    # Miu Miu bags — high demand
    ("Miu Miu", "bags", 290, 58000, "Miu Miu wander bag nappa leather beige", "MIU MIU Сумка Wander нappa бежевая", None),
    ("Miu Miu", "bags", 195, 42000, "Miu Miu crystal embellished mini bag", "MIU MIU Сумка мини с кристаллами", None),
    ("Miu Miu", "shoes", 210, 44000, "Miu Miu ballet flats metallic silver 38", "MIU MIU Балетки металлик серебро", "38"),
    ("Miu Miu", "shoes", 175, 36000, "Miu Miu mary jane shoes patent 37", "MIU MIU Туфли Mary Jane лак", "37"),
    ("Miu Miu", "knitwear", 165, 33000, "Miu Miu cropped mohair cardigan ivory 36", "MIU MIU Кардиган мохер укороченный", "36"),

    # Balenciaga — urban/streetwear
    ("Balenciaga", "bags", 380, 76000, "Balenciaga le cagole shoulder bag black XS", "BALENCIAGA Сумка Le Cagole черная XS", None),
    ("Balenciaga", "bags", 220, 48000, "Balenciaga neo classic mini bag", "BALENCIAGA Сумка Neo Classic мини", None),
    ("Balenciaga", "shoes", 310, 64000, "Balenciaga triple s sneakers white 42", "BALENCIAGA Кроссовки Triple S белые", "42"),
    ("Balenciaga", "shoes", 260, 55000, "Balenciaga speed trainer black 41", "BALENCIAGA Кроссовки Speed черные", "41"),
    ("Balenciaga", "outerwear", 420, 86000, "Balenciaga oversized track jacket black XL", "BALENCIAGA Куртка трек оверсайз черная", "XL"),

    # Maison Margiela — designer resale
    ("Maison Margiela", "shoes", 290, 60000, "Maison Margiela tabi boots black 38", "MAISON MARGIELA Ботинки Tabi черные", "38"),
    ("Maison Margiela", "shoes", 245, 52000, "Maison Margiela replica sneakers white 43", "MAISON MARGIELA Кроссовки Replica белые", "43"),
    ("Maison Margiela", "bags", 280, 57000, "Maison Margiela glam slam medium bag", "MAISON MARGIELA Сумка Glam Slam", None),
    ("Maison Margiela", "knitwear", 145, 31000, "Maison Margiela destroyed knit sweater grey 38", "MAISON MARGIELA Свитер разрушенный трикотаж", "38"),
    ("Maison Margiela", "accessories", 85, 20000, "Maison Margiela zip wallet leather", "MAISON MARGIELA Кошелек кожа на молнии", None),

    # Saint Laurent — classic luxury
    ("Saint Laurent", "bags", 490, 97000, "Saint Laurent loulou medium bag quilted leather", "SAINT LAURENT Сумка Loulou стеганая кожа", None),
    ("Saint Laurent", "bags", 340, 70000, "Saint Laurent sunset medium bag croc effect", "SAINT LAURENT Сумка Sunset под крокодила", None),
    ("Saint Laurent", "bags", 180, 39000, "Saint Laurent envelope clutch leather", "SAINT LAURENT Клатч конверт кожа", None),
    ("Saint Laurent", "shoes", 270, 55000, "Saint Laurent tribute platform sandals black 38", "SAINT LAURENT Сандалии на платформе черные", "38"),
    ("Saint Laurent", "accessories", 120, 26000, "Saint Laurent sunglasses SL 11 black", "SAINT LAURENT Очки солнцезащитные SL 11", None),

    # Gucci — iconic brand
    ("Gucci", "bags", 420, 84000, "Gucci horsebit 1955 shoulder bag GG Supreme", "GUCCI Сумка Horsebit 1955 GG Supreme", None),
    ("Gucci", "bags", 290, 61000, "Gucci marmont mini bag matelassé leather", "GUCCI Сумка Marmont мини стеганая", None),
    ("Gucci", "bags", 195, 41000, "Gucci ophidia mini GG bag", "GUCCI Сумка Ophidia мини GG", None),
    ("Gucci", "shoes", 280, 58000, "Gucci ace sneakers white leather 42", "GUCCI Кроссовки Ace белые кожа", "42"),
    ("Gucci", "accessories", 135, 28000, "Gucci GG marmont belt red leather 80cm", "GUCCI Ремень GG Marmont красный кожа", None),

    # Bottega Veneta — quiet luxury
    ("Bottega Veneta", "bags", 520, 104000, "Bottega Veneta intrecciato pouch clutch black", "BOTTEGA VENETA Клатч плетеная кожа", None),
    ("Bottega Veneta", "bags", 380, 78000, "Bottega Veneta cassette bag padded intrecciato", "BOTTEGA VENETA Сумка Cassette плетение", None),
    ("Bottega Veneta", "shoes", 340, 70000, "Bottega Veneta stretch mules black 38", "BOTTEGA VENETA Мюли стрейч черные", "38"),
    ("Bottega Veneta", "accessories", 160, 34000, "Bottega Veneta intrecciato card case", "BOTTEGA VENETA Картхолдер плетеная кожа", None),

    # Rick Owens — avant-garde
    ("Rick Owens", "outerwear", 490, 99000, "Rick Owens leather biker jacket black 48", "RICK OWENS Байкерская куртка кожа черная", "48"),
    ("Rick Owens", "shoes", 380, 77000, "Rick Owens ramones sneakers white 43", "RICK OWENS Кроссовки Ramones белые", "43"),
    ("Rick Owens", "shoes", 290, 61000, "Rick Owens geobasket sneakers black 42", "RICK OWENS Кроссовки Geobasket черные", "42"),
    ("Rick Owens", "knitwear", 220, 46000, "Rick Owens cashmere hoodie grey 48", "RICK OWENS Худи кашемир серый", "48"),

    # Acne Studios — contemporary
    ("Acne Studios", "bags", 195, 40000, "Acne Studios musubi micro bag dusty pink", "ACNE STUDIOS Сумка Musubi мини пыльная роза", None),
    ("Acne Studios", "outerwear", 320, 65000, "Acne Studios double-breasted suit jacket navy 36", "ACNE STUDIOS Пиджак двубортный темно-синий", "36"),
    ("Acne Studios", "knitwear", 145, 31000, "Acne Studios fairview face sweater grey 38", "ACNE STUDIOS Свитер Fairview лицо серый", "38"),
    ("Acne Studios", "denim", 175, 36000, "Acne Studios 1996 straight jeans indigo 30", "ACNE STUDIOS Джинсы 1996 прямые индиго", "30"),

    # Diesel — premium denim
    ("Diesel", "denim", 110, 23000, "Diesel 1dr shoulder bag black denim", "DIESEL Сумка 1DR деним черная", None),
    ("Diesel", "denim", 130, 28000, "Diesel 2017 bootcut jeans destroyed 30", "DIESEL Джинсы 2017 буткат рваные", "30"),
    ("Diesel", "shoes", 160, 33000, "Diesel s-serendipity sneakers white 42", "DIESEL Кроссовки S-Serendipity белые", "42"),

    # Chrome Hearts — cult brand
    ("Chrome Hearts", "accessories", 245, 51000, "Chrome Hearts cross patch leather bracelet", "CHROME HEARTS Браслет кожа крест", None),
    ("Chrome Hearts", "knitwear", 380, 79000, "Chrome Hearts cross logo hoodie black XL", "CHROME HEARTS Худи логотип крест черный", "XL"),
    ("Chrome Hearts", "accessories", 195, 41000, "Chrome Hearts sterling silver ring size 8", "CHROME HEARTS Кольцо серебро размер 18", None),

    # Comme des Garçons
    ("Comme des Garçons", "knitwear", 180, 38000, "Comme des Garcons heart patch tee red XS", "CDG Футболка сердце красная", "XS"),
    ("Comme des Garçons", "outerwear", 310, 65000, "Comme des Garcons double-breasted blazer black M", "CDG Пиджак двубортный черный", "M"),
    ("Comme des Garçons", "bags", 175, 37000, "Comme des Garcons play zip wallet black", "CDG Кошелек на молнии черный", None),
]


async def run_demo_seed(db) -> dict:
    """Populate DB with demo listings, run matching and scoring. Idempotent."""
    await currency_service.refresh_rates()
    marketplaces = await ensure_marketplaces(db)
    brands = await ensure_brands(db)
    vinted_mp = marketplaces["vinted"]
    oskelly_mp = marketplaces["oskelly"]

    now = datetime.now(UTC)
    vinted_created = 0
    oskelly_created = 0

    for i, (brand_name, category, vinted_price_eur, oskelly_price_rub, v_title, o_title, size) in enumerate(DEMO_LISTINGS):
        brand_slug = slugify(brand_name)
        brand = brands.get(brand_slug)
        if not brand:
            continue

        size_norm, size_sys = normalize_size(size, category) if size else (None, "EU")

        oskelly_eur = rub_to_eur(oskelly_price_rub)
        vinted_rub = (eur(vinted_price_eur) * RUB_RATE).quantize(Decimal("0.01"))
        oskelly_rub_dec = Decimal(str(oskelly_price_rub))

        listed_at = now - timedelta(days=random.randint(1, 30))

        # --- Vinted listing ---
        v_ext_id = f"demo_vinted_{i:04d}"
        existing_v = (await db.execute(
            select(Listing).where(Listing.marketplace_id == vinted_mp.id, Listing.external_id == v_ext_id)
        )).scalar_one_or_none()

        if not existing_v:
            vl = Listing(
                marketplace_id=vinted_mp.id,
                brand_id=brand.id,
                external_id=v_ext_id,
                title=v_title,
                normalized_title=clean_title(v_title, brand.canonical_name),
                category=category,
                subcategory=None,
                size_raw=size,
                size_normalized=size_norm,
                size_system=size_sys,
                condition="excellent",
                price_original=eur(vinted_price_eur),
                currency_original="EUR",
                price_eur=eur(vinted_price_eur),
                price_rub=vinted_rub,
                seller_country="FR",
                listing_url=f"https://www.vinted.fr/items/{v_ext_id}",
                image_urls=[],
                description=v_title,
                is_sold=False,
                is_active=True,
                listed_at=listed_at,
                scraped_at=now,
                raw_data={"source": "vinted", "demo": True},
            )
            db.add(vl)
            await db.flush()
            db.add(PriceHistory(listing_id=vl.id, price_eur=eur(vinted_price_eur), price_rub=vinted_rub, recorded_at=now))
            vinted_created += 1

        # --- Oskelly listing ---
        o_ext_id = f"demo_oskelly_{i:04d}"
        existing_o = (await db.execute(
            select(Listing).where(Listing.marketplace_id == oskelly_mp.id, Listing.external_id == o_ext_id)
        )).scalar_one_or_none()

        if not existing_o:
            ol = Listing(
                marketplace_id=oskelly_mp.id,
                brand_id=brand.id,
                external_id=o_ext_id,
                title=o_title,
                normalized_title=clean_title(o_title, brand.canonical_name),
                category=category,
                subcategory=None,
                size_raw=size,
                size_normalized=size_norm,
                size_system=size_sys,
                condition="excellent",
                price_original=oskelly_rub_dec,
                currency_original="RUB",
                price_eur=oskelly_eur,
                price_rub=oskelly_rub_dec,
                seller_country="RU",
                listing_url=f"https://oskelly.ru/products/demo-{o_ext_id}",
                image_urls=[],
                description=o_title,
                is_sold=False,
                is_active=True,
                listed_at=listed_at,
                scraped_at=now,
                raw_data={"source": "oskelly", "demo": True},
            )
            db.add(ol)
            await db.flush()
            db.add(PriceHistory(listing_id=ol.id, price_eur=oskelly_eur, price_rub=oskelly_rub_dec, recorded_at=now))
            oskelly_created += 1

    await db.flush()

    # Re-run matching and scoring to pick up the new demo listings
    from app.services.pipeline import run_matching, run_scoring
    matches = await run_matching(db)
    scoring = await run_scoring(db)

    return {
        "vinted_listings_created": vinted_created,
        "oskelly_listings_created": oskelly_created,
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
