"""Meilisearch index sync for listings and opportunities (optional)."""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from app.config import get_settings
from app.models import Listing, Opportunity

if TYPE_CHECKING:
    import meilisearch

logger = logging.getLogger(__name__)

LISTINGS_INDEX = "listings"
OPPORTUNITIES_INDEX = "opportunities"


def get_meili_client() -> "meilisearch.Client | None":
    if not get_settings().meilisearch_enabled:
        return None
    try:
        import meilisearch

        settings = get_settings()
        return meilisearch.Client(settings.meilisearch_url, settings.meilisearch_master_key)
    except Exception as exc:
        logger.warning("Meilisearch unavailable: %s", exc)
        return None


def ensure_indexes(client: "meilisearch.Client") -> None:
    for index_name, primary_key in [(LISTINGS_INDEX, "id"), (OPPORTUNITIES_INDEX, "id")]:
        try:
            client.get_index(index_name)
        except Exception:
            client.create_index(index_name, {"primaryKey": primary_key})

    listings = client.index(LISTINGS_INDEX)
    listings.update_filterable_attributes(
        ["brand_slug", "category", "marketplace", "is_active", "price_eur", "size_normalized"]
    )
    listings.update_sortable_attributes(["price_eur", "scraped_at"])

    opps = client.index(OPPORTUNITIES_INDEX)
    opps.update_filterable_attributes(
        ["recommendation", "brand_slug", "category", "roi", "opportunity_score", "risk_score"]
    )
    opps.update_sortable_attributes(["opportunity_score", "roi", "gross_profit_eur"])


def listing_document(listing: Listing, brand_slug: str, marketplace_slug: str) -> dict[str, Any]:
    return {
        "id": str(listing.id),
        "title": listing.title,
        "normalized_title": listing.normalized_title,
        "brand_slug": brand_slug,
        "category": listing.category,
        "subcategory": listing.subcategory,
        "size_normalized": listing.size_normalized,
        "condition": listing.condition,
        "price_eur": float(listing.price_eur),
        "marketplace": marketplace_slug,
        "is_active": listing.is_active,
        "listing_url": listing.listing_url,
        "scraped_at": listing.scraped_at.isoformat() if listing.scraped_at else None,
    }


def opportunity_document(opp: Opportunity) -> dict[str, Any]:
    purchase = opp.purchase_listing
    return {
        "id": str(opp.id),
        "opportunity_score": float(opp.opportunity_score),
        "recommendation": opp.recommendation,
        "roi": float(opp.roi),
        "gross_profit_eur": float(opp.gross_profit_eur),
        "brand_slug": purchase.brand.slug if purchase and purchase.brand else None,
        "category": purchase.category if purchase else None,
        "risk_score": float(opp.risk_score),
        "title": purchase.title if purchase else "",
    }


async def sync_listings(documents: list[dict[str, Any]]) -> None:
    if not documents or not get_settings().meilisearch_enabled:
        return
    client = get_meili_client()
    if not client:
        return
    ensure_indexes(client)
    client.index(LISTINGS_INDEX).add_documents(documents)


async def sync_opportunities(documents: list[dict[str, Any]]) -> None:
    if not documents or not get_settings().meilisearch_enabled:
        return
    client = get_meili_client()
    if not client:
        return
    ensure_indexes(client)
    client.index(OPPORTUNITIES_INDEX).add_documents(documents)
