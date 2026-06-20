"""Unit tests for matching and scoring (no database required)."""

from decimal import Decimal

from app.services.matching import compute_match_confidence, passes_arbitrage_direction
from app.services.normalization import normalize_brand, normalize_size, clean_title
from app.services.scoring import compute_roi_score, compute_price_gap_score


def test_brand_normalization():
    name, conf = normalize_brand("YSL")
    assert name == "Saint Laurent"
    assert conf == 100.0


def test_match_confidence_high():
    scores = compute_match_confidence(
        brand_a="Maison Margiela",
        brand_b="Maison Margiela",
        aliases_a=["Margiela"],
        title_a="tabi ankle boots black",
        title_b="tabi boots black leather",
        category_a="shoes",
        subcategory_a="ankle boots",
        category_b="shoes",
        subcategory_b="ankle boots",
        size_a="38",
        size_b="38",
        has_images=True,
    )
    assert float(scores["match_confidence"]) >= 72


def test_arbitrage_direction():
    assert passes_arbitrage_direction(Decimal("400"), Decimal("800"))
    assert not passes_arbitrage_direction(Decimal("800"), Decimal("400"))


def test_roi_score():
    assert float(compute_roi_score(Decimal("0.75"))) == 62.5
    assert float(compute_roi_score(Decimal("1.2"))) == 100.0


def test_size_normalization():
    size, _ = normalize_size("M", "knitwear", "EU")
    assert size == "38"


if __name__ == "__main__":
    test_brand_normalization()
    test_match_confidence_high()
    test_arbitrage_direction()
    test_roi_score()
    test_size_normalization()
    print("All tests passed")
