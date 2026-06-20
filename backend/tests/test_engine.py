"""Unit tests for matching and scoring (no database required)."""

from decimal import Decimal

from app.services.matching import compute_match_confidence, passes_arbitrage_direction
from app.services.normalization import (
    clean_title,
    detect_item_type,
    item_types_conflict,
    model_match_score,
    normalize_brand,
    normalize_size,
    resolve_semantics,
)
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


def test_detect_item_type_cross_language():
    # English (Vinted) and Russian (Oskelly) resolve to the same vocabulary
    assert detect_item_type("Bottega Veneta Jodie hobo bag") == "bag"
    assert detect_item_type("Сумка тоут Bottega Veneta") == "tote bag"
    assert detect_item_type("Maison Margiela Tabi ankle boots") == "boots"
    assert detect_item_type("Платье Miu Miu шёлк") == "dress"
    assert detect_item_type("nothing recognisable here") is None


def test_item_type_conflict():
    assert item_types_conflict("dress", "t-shirt")        # different knit buckets
    assert item_types_conflict("sneakers", "boots")       # different shoe buckets
    assert not item_types_conflict("bag", "tote bag")     # same bag bucket
    assert not item_types_conflict("sneakers", None)      # one side unknown
    assert not item_types_conflict("shoes", "boots")      # generic type: no gate


def test_model_match_score():
    assert model_match_score("Jodie Bag", "Jodie Bag") == 100.0
    assert model_match_score("Jodie Bag", "Cassette Bag") == 0.0
    assert model_match_score("Jodie Bag", None) is None
    assert model_match_score(None, None) is None


def test_resolve_semantics_registry():
    # Oskelly Russian title with a registry model
    model, item_type = resolve_semantics(
        brand="Balenciaga", category="shoes", subcategory="Кроссовки",
        title="Balenciaga Triple S", description="кроссовки",
    )
    assert model == "Triple S"
    assert item_type == "sneakers"
    # Vinted free text resolves the same model
    model_v, _ = resolve_semantics(
        brand="Balenciaga", category="shoes", subcategory=None,
        title="Balenciaga Triple S sneakers grey", description="",
    )
    assert model_v == "Triple S"


def test_build_russian_listing():
    from app.services.oskelly_publisher import build_russian_listing

    listing = build_russian_listing(
        brand="Bottega Veneta", model="Jodie Bag", item_type="bag",
        category="bags", condition="excellent", size=None, price_rub=185000,
        images=["https://img/1.jpg"],
    )
    # Title is composed in Russian, keeps the Latin model, drops the generic tail
    assert listing.title == "Сумка Bottega Veneta Jodie"
    assert listing.price_rub == 185000
    # Description is generated Russian copy — not a copy of any source text
    assert "Состояние: Отличное состояние" in listing.description
    assert "Bottega Veneta" in listing.description
    assert "Подлинность" in listing.description
    # Size line omitted when no size
    assert "Размер" not in listing.description


def test_build_russian_listing_with_size():
    from app.services.oskelly_publisher import build_russian_listing

    listing = build_russian_listing(
        brand="Maison Margiela", model="Tabi Boots", item_type="boots",
        category="shoes", condition="good", size="39", price_rub=72000,
    )
    assert listing.title == "Ботинки Maison Margiela Tabi"
    assert "Размер: 39" in listing.description
    assert listing.condition_ru == "Хорошее состояние"


def test_match_confidence_model_boost():
    """A confirmed model on both sides scores higher than fuzzy title alone."""
    with_model = compute_match_confidence(
        brand_a="Bottega Veneta", brand_b="Bottega Veneta", aliases_a=["BV"],
        title_a="jodie hobo", title_b="jodie",
        category_a="bags", subcategory_a="bag", category_b="bags", subcategory_b="bag",
        size_a=None, size_b=None, has_images=True,
        model_a="Jodie Bag", model_b="Jodie Bag",
    )
    without_model = compute_match_confidence(
        brand_a="Bottega Veneta", brand_b="Bottega Veneta", aliases_a=["BV"],
        title_a="jodie hobo", title_b="jodie",
        category_a="bags", subcategory_a="bag", category_b="bags", subcategory_b="bag",
        size_a=None, size_b=None, has_images=True,
    )
    assert float(with_model["match_confidence"]) > float(without_model["match_confidence"])
    assert float(with_model["match_confidence"]) >= 72


if __name__ == "__main__":
    test_brand_normalization()
    test_match_confidence_high()
    test_arbitrage_direction()
    test_roi_score()
    test_size_normalization()
    test_detect_item_type_cross_language()
    test_item_type_conflict()
    test_model_match_score()
    test_resolve_semantics_registry()
    test_match_confidence_model_boost()
    print("All tests passed")
