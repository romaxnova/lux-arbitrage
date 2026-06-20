"""Live Vinted scraper using the internal catalog API."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from app.config import get_settings
from app.scrapers.base import MarketplaceAdapter, RawListing
from app.scrapers.http_client import RateLimitedClient
from app.scrapers.vinted_maps import infer_category_from_title, map_vinted_condition

logger = logging.getLogger(__name__)


class VintedAdapter(MarketplaceAdapter):
    slug = "vinted"

    def __init__(self) -> None:
        settings = get_settings()
        self.domain = settings.vinted_domain
        self.per_page = settings.vinted_per_page
        self.max_pages = settings.vinted_max_pages
        self.min_price_eur = settings.vinted_min_price_eur
        self._brand_id_cache: dict[str, int] = {}

    @property
    def base_url(self) -> str:
        return f"https://www.vinted.{self.domain}"

    async def _bootstrap(self, client: RateLimitedClient) -> None:
        await client.get(
            f"{self.base_url}/catalog",
            headers={"Accept": "text/html", "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
        )

    async def _resolve_brand_id(self, client: RateLimitedClient, brand_name: str) -> int | None:
        key = brand_name.lower().strip()
        if key in self._brand_id_cache:
            return self._brand_id_cache[key]

        response = await client.get(
            f"{self.base_url}/api/v2/brands",
            params={"keyword": brand_name},
            headers={"Accept": "application/json", "Accept-Language": "fr-FR,fr;q=0.9"},
        )
        if response.status_code != 200:
            return None

        brands = response.json().get("brands", [])
        exact = next((b for b in brands if b.get("title", "").lower() == key), None)
        if not exact:
            exact = next((b for b in brands if key in b.get("title", "").lower()), None)
        if not exact:
            return None

        brand_id = int(exact["id"])
        self._brand_id_cache[key] = brand_id
        return brand_id

    def _parse_item(self, item: dict, brand_name: str, category: str) -> RawListing | None:
        if not item.get("is_visible", True):
            return None

        price_data = item.get("price") or {}
        amount = price_data.get("amount")
        if amount is None:
            return None

        price = Decimal(str(amount))
        if price < Decimal(str(self.min_price_eur)):
            return None

        photos = item.get("photos") or []
        image_urls = [p.get("url") for p in photos if p.get("url")]
        if not image_urls and item.get("photo", {}).get("url"):
            image_urls = [item["photo"]["url"]]

        title = item.get("title") or ""
        item_id = str(item["id"])
        inferred_cat = category if category != "all" else infer_category_from_title(title)

        listed_at = None
        if photos and photos[0].get("high_resolution", {}).get("timestamp"):
            listed_at = datetime.fromtimestamp(photos[0]["high_resolution"]["timestamp"], tz=UTC)

        return RawListing(
            external_id=item_id,
            brand=item.get("brand_title") or brand_name,
            title=title,
            category=inferred_cat,
            subcategory=None,
            size_raw=item.get("size_title") or None,
            size_system="EU",
            condition=map_vinted_condition(item.get("status")),
            price=price,
            currency=price_data.get("currency_code", "EUR"),
            seller_country=self.domain.upper()[:2] if len(self.domain) == 2 else "FR",
            listing_url=item.get("url") or f"{self.base_url}/items/{item_id}",
            image_urls=image_urls,
            description=item.get("item_box", {}).get("accessibility_label", title),
            is_sold=False,
            listed_at=listed_at,
        )

    async def fetch_listings(self, brand: str, category: str, limit: int = 20) -> list[RawListing]:
        listings: list[RawListing] = []
        seen_ids: set[str] = set()

        async with RateLimitedClient(requests_per_second=0.8) as client:
            await self._bootstrap(client)
            brand_id = await self._resolve_brand_id(client, brand)
            if not brand_id:
                logger.warning("Vinted brand not found: %s", brand)
                return []

            for page in range(1, self.max_pages + 1):
                if len(listings) >= limit:
                    break

                params: dict = {
                    "brand_ids[]": brand_id,
                    "per_page": min(self.per_page, 96),
                    "page": page,
                    "order": "newest_first",
                    "price_from": self.min_price_eur,
                }

                response = await client.get(
                    f"{self.base_url}/api/v2/catalog/items",
                    params=params,
                    headers={"Accept": "application/json", "Accept-Language": "fr-FR,fr;q=0.9"},
                )
                if response.status_code != 200:
                    logger.error("Vinted catalog error %s: %s", response.status_code, response.text[:200])
                    break

                items = response.json().get("items", [])
                if not items:
                    break

                for item in items:
                    parsed = self._parse_item(item, brand, category)
                    if not parsed or parsed.external_id in seen_ids:
                        continue
                    if category != "all" and parsed.category != category:
                        continue
                    seen_ids.add(parsed.external_id)
                    listings.append(parsed)
                    if len(listings) >= limit:
                        break

        logger.info("Vinted fetched %s listings for brand=%s category=%s", len(listings), brand, category)
        return listings
