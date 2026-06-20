from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class RawListing:
    external_id: str
    brand: str
    title: str
    category: str
    subcategory: str | None
    size_raw: str | None
    size_system: str
    condition: str
    price: Decimal
    currency: str
    seller_country: str
    listing_url: str
    image_urls: list[str]
    description: str
    is_sold: bool
    listed_at: datetime | None
    model_name: str | None = None   # structured model name (e.g. "Jodie", "Cassette")


class MarketplaceAdapter(ABC):
    slug: str

    @abstractmethod
    async def fetch_listings(self, brand: str, category: str, limit: int = 20) -> list[RawListing]:
        ...
