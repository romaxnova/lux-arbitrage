"""
Vinted scraper via Vercel proxy.

Vinted blocks non-European IPs (Render's servers are in the US).
The Vercel frontend runs from Frankfurt (fra1), which CAN access Vinted.
This adapter calls the /api/vinted proxy route so the actual Vinted
request originates from a European IP.

Set VINTED_PROXY_URL=https://your-app.vercel.app in Render env vars.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.config import get_settings
from app.scrapers.base import MarketplaceAdapter, RawListing
from app.scrapers.vinted_maps import infer_category_from_title, map_vinted_condition

logger = logging.getLogger(__name__)

CONDITION_MAP = {
    "new with tags": "new",
    "neuf avec étiquette": "new",
    "new without tags": "excellent",
    "very good": "excellent",
    "good": "good",
    "satisfactory": "fair",
}


class VintedProxyAdapter(MarketplaceAdapter):
    """Fetches Vinted data via the Vercel /api/vinted proxy endpoint."""

    slug = "vinted"

    def __init__(self) -> None:
        settings = get_settings()
        self.proxy_url = settings.vinted_proxy_url.rstrip("/")
        self.min_price_eur = settings.vinted_min_price_eur

    def _available(self) -> bool:
        return bool(self.proxy_url)

    async def fetch_listings(
        self,
        brand: str,
        category: str,
        limit: int = 20,
        item_type_en: str = "",
    ) -> list[RawListing]:
        if not self._available():
            return []

        endpoint = f"{self.proxy_url}/api/vinted"
        params: dict = {"brand": brand, "limit": limit, "min_price": str(self.min_price_eur)}
        if item_type_en:
            params["item_type"] = item_type_en

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(endpoint, params=params)
                if resp.status_code != 200:
                    logger.warning("Vinted proxy returned %s for brand=%s", resp.status_code, brand)
                    return []
                data = resp.json()
        except Exception as exc:
            logger.warning("Vinted proxy request failed for brand=%s: %s", brand, exc)
            return []

        raw_items = data.get("items", [])
        listings: list[RawListing] = []

        for item in raw_items:
            title = item.get("title") or ""
            inferred_cat = category if category != "all" else infer_category_from_title(title)
            if category != "all" and inferred_cat != category:
                continue

            price_eur = float(item.get("price_eur") or 0)
            if price_eur < self.min_price_eur:
                continue

            image_url = item.get("image_url")
            listings.append(
                RawListing(
                    external_id=str(item["id"]),
                    brand=item.get("brand") or brand,
                    title=title,
                    category=inferred_cat,
                    subcategory=None,
                    size_raw=item.get("size") or None,
                    size_system="EU",
                    condition=map_vinted_condition(item.get("condition")),
                    price=__import__("decimal").Decimal(str(price_eur)),
                    currency="EUR",
                    seller_country="FR",
                    listing_url=item.get("url") or f"https://www.vinted.fr/items/{item['id']}",
                    image_urls=[image_url] if image_url else [],
                    description=title,
                    is_sold=False,
                    listed_at=datetime.now(UTC),
                )
            )

        logger.info("Vinted proxy fetched %s listings for brand=%s", len(listings), brand)
        return listings
