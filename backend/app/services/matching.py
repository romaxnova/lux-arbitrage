from decimal import Decimal

from app.core.constants import MATCH_WEIGHTS
from app.services.normalization import (
    brand_match_score,
    category_match_score,
    size_match_score,
    title_match_score,
)


def compute_match_confidence(
    *,
    brand_a: str,
    brand_b: str,
    aliases_a: list[str] | None,
    title_a: str,
    title_b: str,
    category_a: str,
    subcategory_a: str | None,
    category_b: str,
    subcategory_b: str | None,
    size_a: str | None,
    size_b: str | None,
    has_images: bool = False,
) -> dict[str, Decimal]:
    brand_score = brand_match_score(brand_a, brand_b, aliases_a)
    title_score = title_match_score(title_a, title_b)
    category_score = category_match_score(category_a, subcategory_a, category_b, subcategory_b)
    size_score = size_match_score(size_a, size_b, category_a)
    image_score = Decimal("60.0") if has_images else Decimal("0.0")

    weights = dict(MATCH_WEIGHTS)
    if not has_images:
        weights["title"] += 0.12
        weights["brand"] += 0.08
        weights["image"] = 0.0

    confidence = (
        Decimal(str(weights["brand"])) * Decimal(str(brand_score))
        + Decimal(str(weights["title"])) * Decimal(str(title_score))
        + Decimal(str(weights["image"])) * image_score
        + Decimal(str(weights["category"])) * Decimal(str(category_score))
        + Decimal(str(weights["size"])) * Decimal(str(size_score))
    )

    return {
        "match_confidence": confidence.quantize(Decimal("0.01")),
        "brand_score": Decimal(str(brand_score)).quantize(Decimal("0.01")),
        "title_score": Decimal(str(title_score)).quantize(Decimal("0.01")),
        "image_score": image_score.quantize(Decimal("0.01")),
        "category_score": Decimal(str(category_score)).quantize(Decimal("0.01")),
        "size_score": Decimal(str(size_score)).quantize(Decimal("0.01")),
    }


def passes_arbitrage_direction(source_price_eur: Decimal, target_price_eur: Decimal) -> bool:
    return source_price_eur < target_price_eur * Decimal("0.95")
