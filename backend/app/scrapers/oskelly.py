"""Live Oskelly scraper via Nuxt catalog pages."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from app.config import get_settings
from app.scrapers.base import MarketplaceAdapter, RawListing
from app.scrapers.http_client import RateLimitedClient
from app.scrapers.nuxt import extract_products_from_catalog

logger = logging.getLogger(__name__)


class OskellyAdapter(MarketplaceAdapter):
    slug = "oskelly"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.oskelly_base_url.rstrip("/")
        self.max_pages = settings.oskelly_max_pages
        self.min_price_rub = settings.oskelly_min_price_rub

    async def fetch_listings(self, brand: str, category: str, limit: int = 20) -> list[RawListing]:
        listings: list[RawListing] = []
        seen_ids: set[str] = set()
        search_query = brand if brand != "all" else "luxury"

        async with RateLimitedClient(requests_per_second=0.5) as client:
            for page in range(1, self.max_pages + 1):
                if len(listings) >= limit:
                    break

                url = f"{self.base_url}/catalog?search={search_query}&page={page}"
                response = await client.get(
                    url,
                    headers={"Accept": "text/html", "Accept-Language": "ru-RU,ru;q=0.9"},
                )
                if response.status_code != 200:
                    logger.error("Oskelly catalog error %s", response.status_code)
                    break

                products = extract_products_from_catalog(response.text)
                if not products:
                    break

                for product in products:
                    ext_id = product["external_id"]
                    if ext_id in seen_ids:
                        continue

                    price = Decimal(str(product["price"]))
                    if price < Decimal(str(self.min_price_rub)):
                        continue

                    if category != "all" and product["category"] != category:
                        continue

                    # Filter by brand match when searching broad queries
                    if brand != "all" and brand.lower() not in product["brand"].lower():
                        continue

                    seen_ids.add(ext_id)
                    listings.append(
                        RawListing(
                            external_id=ext_id,
                            brand=product["brand"],
                            title=product["title"],
                            category=product["category"],
                            subcategory=product.get("subcategory"),
                            size_raw=product.get("size_raw"),
                            size_system=product.get("size_system", "EU"),
                            condition=product["condition"],
                            price=price,
                            currency="RUB",
                            seller_country="RU",
                            listing_url=product["listing_url"],
                            image_urls=product.get("image_urls") or [],
                            description=product.get("description") or "",
                            is_sold=product.get("is_sold", False),
                            listed_at=datetime.now(UTC),
                        )
                    )
                    if len(listings) >= limit:
                        break

        logger.info("Oskelly fetched %s listings for brand=%s category=%s", len(listings), brand, category)
        return listings
