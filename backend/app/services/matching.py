from decimal import Decimal

from app.core.constants import MATCH_WEIGHTS
from app.services.normalization import (
    brand_match_score,
    category_match_score,
    model_match_score,
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
    model_a: str | None = None,
    model_b: str | None = None,
) -> dict[str, Decimal]:
    brand_score = brand_match_score(brand_a, brand_b, aliases_a)
    title_score = title_match_score(title_a, title_b)
    category_score = category_match_score(category_a, subcategory_a, category_b, subcategory_b)
    size_score = size_match_score(size_a, size_b, category_a)
    image_score = 60.0 if has_images else 0.0
    model_score = model_match_score(model_a, model_b)

    # Availability-normalised weighting: only signals that exist for this pair
    # contribute, and the confidence is the weighted mean over them. This keeps
    # scores comparable whether or not a model/image signal is present, instead
    # of ad-hoc per-case weight tweaks.
    w = MATCH_WEIGHTS
    contributions: list[tuple[float, float]] = [
        (w["brand"], brand_score),
        (w["title"], title_score),
        (w["category"], category_score),
        (w["size"], size_score),
    ]
    if has_images:
        contributions.append((w["image"], image_score))
    if model_score is not None:
        contributions.append((w["model"], model_score))

    total_weight = sum(weight for weight, _ in contributions)
    weighted = sum(weight * score for weight, score in contributions)
    confidence = Decimal(str(weighted / total_weight)) if total_weight else Decimal("0")

    return {
        "match_confidence": confidence.quantize(Decimal("0.01")),
        "brand_score": Decimal(str(brand_score)).quantize(Decimal("0.01")),
        "title_score": Decimal(str(title_score)).quantize(Decimal("0.01")),
        "image_score": Decimal(str(image_score)).quantize(Decimal("0.01")),
        "category_score": Decimal(str(category_score)).quantize(Decimal("0.01")),
        "size_score": Decimal(str(size_score)).quantize(Decimal("0.01")),
    }


def passes_arbitrage_direction(source_price_eur: Decimal, target_price_eur: Decimal) -> bool:
    return source_price_eur < target_price_eur * Decimal("0.95")
