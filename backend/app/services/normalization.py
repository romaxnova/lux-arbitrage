import re
import unicodedata
from decimal import Decimal

from rapidfuzz import fuzz

from app.core.constants import (
    BRAND_ALIASES,
    CLOTHING_SIZE_MAP,
    CONDITION_MAP,
    NOISE_WORDS,
    SHOE_SIZE_MAP,
)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def normalize_brand(raw_brand: str, brand_lookup: dict[str, str] | None = None) -> tuple[str, float]:
    """Return (canonical_name, confidence)."""
    raw = raw_brand.strip()
    if not raw:
        return "Unknown", 0.0

    lookup = brand_lookup or {}
    for canonical, aliases in BRAND_ALIASES.items():
        lookup[canonical.lower()] = canonical
        for alias in aliases:
            lookup[alias.lower()] = canonical

    lower = raw.lower()
    if lower in lookup:
        return lookup[lower], 100.0

    best_name, best_score = "Unknown", 0.0
    for canonical, aliases in BRAND_ALIASES.items():
        candidates = [canonical] + aliases
        for candidate in candidates:
            score = fuzz.ratio(lower, candidate.lower())
            if score > best_score:
                best_score = score
                best_name = canonical

    if best_score >= 85:
        return best_name, float(best_score)
    return raw, float(best_score)


def clean_title(title: str, brand: str | None = None) -> str:
    text = title.lower()
    if brand:
        for part in brand.lower().split():
            text = text.replace(part, " ")
    tokens = []
    # Use \w to capture Unicode word chars (Latin, Cyrillic, etc.) plus digits
    for token in re.findall(r"[\w]+", text, re.UNICODE):
        if token not in NOISE_WORDS and len(token) > 1:
            tokens.append(token)
    return " ".join(tokens)


def normalize_condition(raw: str) -> str:
    return CONDITION_MAP.get(raw.lower().strip(), "good")


def normalize_size(raw_size: str | None, category: str, size_system: str = "EU") -> tuple[str | None, str]:
    if not raw_size:
        return None, size_system

    raw = raw_size.strip().upper()
    if raw in ("ONE SIZE", "OS", "UNICA", "TU"):
        return "ONE_SIZE", "EU"

    size_map = SHOE_SIZE_MAP if category == "shoes" else CLOTHING_SIZE_MAP
    system_map = size_map.get(size_system.upper(), size_map.get("EU", {}))

    if raw in system_map:
        return system_map[raw], "EU"

    # Try US letter sizes for clothing when EU numeric map misses
    if category != "shoes" and raw in CLOTHING_SIZE_MAP["US"]:
        return CLOTHING_SIZE_MAP["US"][raw], "EU"

    match = re.search(r"(\d+(?:\.\d)?)", raw)
    if match:
        return match.group(1), size_system

    return raw, size_system


def size_match_score(size_a: str | None, size_b: str | None, category: str) -> float:
    if not size_a or not size_b:
        return 50.0 if category in ("bags", "accessories", "jewelry", "eyewear") else 0.0
    if size_a == "ONE_SIZE" and size_b == "ONE_SIZE":
        return 100.0
    if size_a == size_b:
        return 100.0
    try:
        diff = abs(float(size_a) - float(size_b))
        if category == "shoes":
            if diff <= 0.5:
                return 80.0
            if diff <= 1.0:
                return 50.0
        return 0.0
    except ValueError:
        return 100.0 if size_a == size_b else 0.0


def category_match_score(cat_a: str, sub_a: str | None, cat_b: str, sub_b: str | None) -> float:
    if cat_a == cat_b and sub_a and sub_b and sub_a == sub_b:
        return 100.0
    if cat_a == cat_b:
        return 85.0
    related = {"outerwear", "knitwear"}
    if cat_a in related and cat_b in related:
        return 30.0
    return 0.0


def brand_match_score(name_a: str, name_b: str, aliases_a: list[str] | None = None) -> float:
    if name_a.lower() == name_b.lower():
        return 100.0
    all_a = [name_a.lower()] + [a.lower() for a in (aliases_a or [])]
    if name_b.lower() in all_a:
        return 100.0
    return float(fuzz.ratio(name_a.lower(), name_b.lower()))


def title_match_score(title_a: str, title_b: str) -> float:
    return float(fuzz.token_set_ratio(title_a, title_b))
