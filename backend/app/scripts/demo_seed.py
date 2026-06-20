"""
Model-aware seed: only pair listings where the exact product model is known.

Strategy:
1. Scrape Oskelly for all brands (no EUR floor — we want everything with a model).
2. For each listing, identify the model via:
   a. productModel.name (structured Oskelly field)
   b. find_model(brand, title + description) against the BRAND_MODELS registry
   Listings with no identified model are DISCARDED.
3. For each (brand, model) pair, call the Vinted proxy with
   brand_id + model search terms (e.g. 'Jodie bag', 'Triple S sneakers').
4. Validate returned Vinted listings against the same model registry.
5. Match only when both sides confirm the same canonical model.

This eliminates 'apples vs oranges' matching at the root level.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import quote_plus

from sqlalchemy import select

from app.core.models_guide import BRAND_MODELS, find_model
from app.database import AsyncSessionLocal, init_db
from app.models import Listing, Marketplace, PriceHistory
from app.scrapers.oskelly import OskellyAdapter
from app.services.currency import currency_service
from app.services.normalization import clean_title, normalize_size, slugify
from app.services.pipeline import ensure_brands, ensure_marketplaces, run_matching, run_scoring

logger = logging.getLogger(__name__)

MIN_GROSS_PROFIT_EUR = 250


def _estimate_profit(oskelly_eur: float, vinted_eur: float) -> float:
    shipping = 10.0
    buyer_fee = vinted_eur * 0.05 + 0.70
    import_cost = (vinted_eur + shipping) * 0.15
    return oskelly_eur - (vinted_eur + shipping + buyer_fee + import_cost)


async def _upsert(db, *, mp, brand, ext_id, title, category, subcategory, size_raw,
                  price_eur, currency, listing_url, image_urls, description):
    existing = (await db.execute(
        select(Listing).where(Listing.marketplace_id == mp.id, Listing.external_id == ext_id)
    )).scalar_one_or_none()
    if existing:
        return existing

    rub_rate = currency_service.get_rate("RUB")
    eur_price = (price_eur / rub_rate).quantize(Decimal("0.01")) if currency == "RUB" else price_eur
    rub_price = (eur_price * rub_rate).quantize(Decimal("0.01"))
    size_norm, size_sys = normalize_size(size_raw, category) if size_raw else (None, "EU")
    now = datetime.now(UTC)

    listing = Listing(
        marketplace_id=mp.id, brand_id=brand.id, external_id=ext_id,
        title=title, normalized_title=clean_title(title, brand.canonical_name),
        category=category, subcategory=subcategory,
        size_raw=size_raw, size_normalized=size_norm, size_system=size_sys,
        condition="excellent",
        price_original=eur_price if currency == "EUR" else price_eur,
        currency_original=currency, price_eur=eur_price, price_rub=rub_price,
        seller_country="RU" if mp.slug == "oskelly" else "FR",
        listing_url=listing_url, image_urls=image_urls,
        description=description, is_sold=False, is_active=True,
        listed_at=now, scraped_at=now, raw_data={"source": mp.slug, "demo": True},
    )
    db.add(listing)
    await db.flush()
    db.add(PriceHistory(listing_id=listing.id, price_eur=eur_price, price_rub=rub_price, recorded_at=now))
    return listing


async def _fetch_vinted_for_model(brand_name: str, model_entry: dict, proxy_url: str) -> list[dict]:
    """Search Vinted specifically for brand + model search phrase."""
    if not proxy_url:
        return []
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{proxy_url.rstrip('/')}/api/vinted",
                params={
                    "brand": brand_name,
                    "item_type": model_entry["search_en"],
                    "limit": 8,
                    "min_price": "60",
                },
            )
            if r.status_code == 200:
                return r.json().get("items", [])
    except Exception as exc:
        logger.warning("Vinted proxy error for %s %s: %s", brand_name, model_entry["canonical"], exc)
    return []


def _validate_vinted_listing(item: dict, model_entry: dict) -> bool:
    """Return True if the Vinted listing text confirms the expected model."""
    text = (item.get("title") or "").lower() + " " + (item.get("brand") or "").lower()
    # Must match at least one alias from the model
    if any(alias in text for alias in model_entry["aliases"]):
        return True
    # Accept if item brand is correct and search_en keywords appear in title
    search_words = model_entry["search_en"].lower().split()
    if sum(1 for w in search_words if w in text) >= max(1, len(search_words) - 1):
        return True
    return False


async def run_demo_seed(db) -> dict:
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
    # (brand_slug, model_canonical) → Vinted ext_id already seeded
    seeded_vinted: dict[tuple[str, str], str] = {}

    for brand_name in PRIORITY_BRANDS:
        brand_slug = slugify(brand_name)
        brand = brands.get(brand_slug)
        if not brand:
            continue

        if brand_name not in BRAND_MODELS:
            logger.info("No model guide for %s — skipping", brand_name)
            continue

        try:
            raw_listings = await adapter.fetch_listings(brand_name, "all", limit=40)
        except Exception as exc:
            logger.warning("Oskelly scrape failed for %s: %s", brand_name, exc)
            continue

        for raw in raw_listings:
            if raw.is_sold:
                continue

            # -- Model identification --
            # 1. Structured productModel.name from Oskelly
            model_entry = None
            if raw.model_name:
                # Try to match the structured model name against our registry
                model_entry = find_model(brand_name, raw.model_name)

            # 2. Fall back to title + description search
            if not model_entry:
                full_text = (raw.title or "") + " " + (raw.description or "")
                model_entry = find_model(brand_name, full_text)

            if not model_entry:
                logger.debug("No model found for '%s' — skipping", raw.title)
                continue

            if raw.currency == "RUB":
                oskelly_eur = float(raw.price / rub_rate)
            else:
                oskelly_eur = float(raw.price)

            # -- Oskelly listing --
            o_ext_id = f"mo_{raw.external_id}"
            # Use the canonical model name in the title for clarity
            display_title = f"{raw.brand} {model_entry['canonical']}"
            ol = await _upsert(
                db, mp=oskelly_mp, brand=brand,
                ext_id=o_ext_id,
                title=display_title,
                category=model_entry["category"],
                subcategory=model_entry["canonical"],   # ← canonical model name as subcategory
                size_raw=raw.size_raw,
                price_eur=Decimal(str(raw.price)),
                currency=raw.currency,
                listing_url=raw.listing_url,
                image_urls=raw.image_urls,
                description=raw.description or display_title,
            )
            if ol:
                oskelly_created += 1

            # -- Vinted listing: one per (brand, model) --
            vinted_key = (brand_slug, model_entry["canonical"])
            if vinted_key not in seeded_vinted:
                vinted_items = await _fetch_vinted_for_model(brand_name, model_entry, proxy_url)

                # Filter to only listings that confirm the model
                valid = [
                    i for i in vinted_items
                    if i.get("price_eur", 0) >= 60
                    and _validate_vinted_listing(i, model_entry)
                    and _estimate_profit(oskelly_eur, i["price_eur"]) >= MIN_GROSS_PROFIT_EUR
                ]

                best = None
                if valid:
                    # Prefer listings with an image, then highest price (best condition signal)
                    best = sorted(valid, key=lambda i: (bool(i.get("image_url")), i["price_eur"]), reverse=True)[0]

                if best:
                    v_ext_id = f"vm_{brand_slug}_{slugify(model_entry['canonical'])}"
                    vl = await _upsert(
                        db, mp=vinted_mp, brand=brand,
                        ext_id=v_ext_id,
                        title=best["title"],
                        category=model_entry["category"],
                        subcategory=model_entry["canonical"],  # ← same canonical
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
                else:
                    # Fallback: Vinted search URL
                    v_ext_id = f"vs_{brand_slug}_{slugify(model_entry['canonical'])}"
                    vinted_eur = Decimal(str(round(oskelly_eur * 0.40, 2)))
                    vl = await _upsert(
                        db, mp=vinted_mp, brand=brand,
                        ext_id=v_ext_id,
                        title=f"{brand_name} {model_entry['canonical']}",
                        category=model_entry["category"],
                        subcategory=model_entry["canonical"],
                        size_raw=None,
                        price_eur=vinted_eur,
                        currency="EUR",
                        listing_url=f"https://www.vinted.fr/catalog?search_text={quote_plus(brand_name + ' ' + model_entry['search_en'])}",
                        image_urls=[],
                        description=f"Search Vinted: {brand_name} {model_entry['search_en']}",
                    )
                    if vl:
                        vinted_created += 1
                    seeded_vinted[vinted_key] = v_ext_id

    await db.flush()
    matches = await run_matching(db)
    scoring = await run_scoring(db)

    return {
        "oskelly_with_model": oskelly_created,
        "vinted_listings": vinted_created,
        "matches": matches,
        "opportunities_created": scoring["created"],
        "opportunities_updated": scoring["updated"],
    }


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        stats = await run_demo_seed(db)
        await db.commit()
        print("Model-aware seed complete:", stats)


if __name__ == "__main__":
    asyncio.run(main())
