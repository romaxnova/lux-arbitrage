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

# Maps Russian keyword fragments (case-insensitive) to an English item-type
# search phrase used when querying Vinted for matching listings.
# Ordered from most-specific to least-specific — first match wins.
RUSSIAN_TO_ITEM_TYPE: list[tuple[str, str, str]] = [
    # shoes
    ("кроссовк", "shoes", "sneakers"),
    ("кроссов",  "shoes", "sneakers"),
    ("сникер",   "shoes", "sneakers"),
    ("ботинк",   "shoes", "boots"),
    ("ботин",    "shoes", "boots"),
    ("сапог",    "shoes", "boots"),
    ("туфл",     "shoes", "heels"),
    ("балетк",   "shoes", "ballet flats"),
    ("балетки",  "shoes", "ballet flats"),
    ("лофер",    "shoes", "loafers"),
    ("мюли",     "shoes", "mules"),
    ("сандал",   "shoes", "sandals"),
    ("босоножк", "shoes", "sandals"),
    ("слипон",   "shoes", "slip-on"),
    ("кед",      "shoes", "sneakers"),
    ("обув",     "shoes", "shoes"),
    ("эспадрил", "shoes", "espadrilles"),
    ("кабоши",   "shoes", "shoes"),
    # bags
    ("тоут",     "bags",  "tote bag"),
    ("шоппер",   "bags",  "shopper bag"),
    ("клатч",    "bags",  "clutch"),
    ("кошел",    "bags",  "wallet"),
    ("кошелек",  "bags",  "wallet"),
    ("рюкзак",   "bags",  "backpack"),
    ("поясн",    "bags",  "belt bag"),
    ("сумк",     "bags",  "bag"),
    ("сумка",    "bags",  "bag"),
    ("портфел",  "bags",  "briefcase"),
    # outerwear
    ("пухов",    "outerwear", "down jacket"),
    ("бомбер",   "outerwear", "bomber jacket"),
    ("анорак",   "outerwear", "anorak"),
    ("пальт",    "outerwear", "coat"),
    ("куртк",    "outerwear", "jacket"),
    ("плащ",     "outerwear", "raincoat"),
    ("жилет",    "outerwear", "vest"),
    # denim / trousers
    ("джинс",    "denim",   "jeans"),
    ("брюки",    "denim",   "trousers"),
    ("брюк",     "denim",   "trousers"),
    ("шорт",     "denim",   "shorts"),
    # knitwear / tops
    ("кардиган", "knitwear", "cardigan"),
    ("пуловер",  "knitwear", "pullover"),
    ("свитер",   "knitwear", "sweater"),
    ("худи",     "knitwear", "hoodie"),
    ("толстов",  "knitwear", "sweatshirt"),
    ("поло",     "knitwear", "polo shirt"),
    ("лонгслив", "knitwear", "long sleeve"),
    ("футболк",  "knitwear", "t-shirt"),
    ("футбол",   "knitwear", "t-shirt"),
    ("рубашк",   "knitwear", "shirt"),
    ("рубаш",    "knitwear", "shirt"),
    ("блуз",     "knitwear", "blouse"),
    ("топ",      "knitwear", "top"),
    ("плать",    "knitwear", "dress"),
    ("юбк",      "knitwear", "skirt"),
    # jewelry
    ("колье",    "jewelry",  "necklace"),
    ("серьг",    "jewelry",  "earrings"),
    ("кулон",    "jewelry",  "pendant"),
    ("браслет",  "jewelry",  "bracelet"),
    ("кольц",    "jewelry",  "ring"),
    ("цепочк",   "jewelry",  "chain"),
    ("кольцо",   "jewelry",  "ring"),
    # eyewear
    ("солнцезащ","eyewear",  "sunglasses"),
    ("очки",     "eyewear",  "sunglasses"),
    ("очк",      "eyewear",  "sunglasses"),
]


def extract_item_type(title: str) -> tuple[str, str]:
    """Return (category, english_search_phrase) from a Russian Oskelly title.

    Uses the first matching Russian keyword fragment.
    Falls back to ("accessories", "") when nothing matches.
    """
    lower = title.lower()
    for fragment, category, english in RUSSIAN_TO_ITEM_TYPE:
        if fragment in lower:
            return category, english
    return "accessories", ""


# English/European keyword fragments -> (category, canonical item type).
# Mirrors RUSSIAN_TO_ITEM_TYPE so Vinted (EN/FR/IT/DE/NL) titles resolve to the
# same canonical item-type vocabulary as Oskelly. Most-specific first.
ENGLISH_TO_ITEM_TYPE: list[tuple[str, str, str]] = [
    # shoes
    ("sneaker", "shoes", "sneakers"), ("trainer", "shoes", "sneakers"),
    ("basket", "shoes", "sneakers"), ("runner", "shoes", "sneakers"),
    ("ankle boot", "shoes", "boots"), ("boot", "shoes", "boots"),
    ("stiefel", "shoes", "boots"), ("bottine", "shoes", "boots"),
    ("loafer", "shoes", "loafers"), ("mocassin", "shoes", "loafers"),
    ("mocassino", "shoes", "loafers"),
    ("ballet", "shoes", "ballet flats"), ("ballerina", "shoes", "ballet flats"),
    ("ballerine", "shoes", "ballet flats"),
    ("espadrille", "shoes", "espadrilles"),
    ("mule", "shoes", "mules"), ("sabot", "shoes", "mules"),
    ("sandal", "shoes", "sandals"), ("sandale", "shoes", "sandals"),
    ("heel", "shoes", "heels"), ("pump", "shoes", "heels"),
    ("talon", "shoes", "heels"), ("escarpin", "shoes", "heels"),
    ("slingback", "shoes", "heels"), ("derby", "shoes", "loafers"),
    ("slip-on", "shoes", "sneakers"), ("slipon", "shoes", "sneakers"),
    ("flat", "shoes", "ballet flats"),
    ("chaussure", "shoes", "shoes"), ("scarpa", "shoes", "shoes"),
    ("schuh", "shoes", "shoes"), ("tabi", "shoes", "boots"),
    # bags
    ("tote", "bags", "tote bag"), ("shopper", "bags", "tote bag"),
    ("backpack", "bags", "backpack"), ("rucksack", "bags", "backpack"),
    ("sac a dos", "bags", "backpack"), ("sac à dos", "bags", "backpack"),
    ("belt bag", "bags", "belt bag"), ("bum bag", "bags", "belt bag"),
    ("clutch", "bags", "clutch"), ("pochette", "bags", "clutch"),
    ("pouch", "bags", "clutch"),
    ("wallet", "bags", "wallet"), ("portefeuille", "bags", "wallet"),
    ("porte-monnaie", "bags", "wallet"), ("portafoglio", "bags", "wallet"),
    ("briefcase", "bags", "briefcase"),
    ("crossbody", "bags", "bag"), ("shoulder bag", "bags", "bag"),
    ("hobo", "bags", "bag"), ("bag", "bags", "bag"), ("sac", "bags", "bag"),
    ("borsa", "bags", "bag"), ("tasche", "bags", "bag"),
    # outerwear
    ("down jacket", "outerwear", "down jacket"), ("puffer", "outerwear", "down jacket"),
    ("doudoune", "outerwear", "down jacket"),
    ("bomber", "outerwear", "bomber jacket"), ("anorak", "outerwear", "anorak"),
    ("parka", "outerwear", "anorak"),
    ("raincoat", "outerwear", "raincoat"), ("trench", "outerwear", "raincoat"),
    ("coat", "outerwear", "coat"), ("manteau", "outerwear", "coat"),
    ("cappotto", "outerwear", "coat"), ("mantel", "outerwear", "coat"),
    ("jacket", "outerwear", "jacket"), ("veste", "outerwear", "jacket"),
    ("blouson", "outerwear", "jacket"), ("giacca", "outerwear", "jacket"),
    ("jacke", "outerwear", "jacket"), ("vest", "outerwear", "vest"),
    ("gilet", "outerwear", "vest"),
    # denim / trousers
    ("jean", "denim", "jeans"), ("denim", "denim", "jeans"),
    ("trouser", "denim", "trousers"), ("pantalon", "denim", "trousers"),
    ("short", "denim", "shorts"),
    # knitwear / tops
    ("cardigan", "knitwear", "cardigan"),
    ("pullover", "knitwear", "pullover"), ("pull", "knitwear", "pullover"),
    ("sweater", "knitwear", "sweater"), ("jumper", "knitwear", "sweater"),
    ("maglione", "knitwear", "sweater"),
    ("hoodie", "knitwear", "hoodie"), ("sweat", "knitwear", "sweatshirt"),
    ("polo", "knitwear", "polo shirt"),
    ("long sleeve", "knitwear", "long sleeve"), ("longsleeve", "knitwear", "long sleeve"),
    ("t-shirt", "knitwear", "t-shirt"), ("tee", "knitwear", "t-shirt"),
    ("tshirt", "knitwear", "t-shirt"), ("t shirt", "knitwear", "t-shirt"),
    ("shirt", "knitwear", "shirt"), ("chemise", "knitwear", "shirt"),
    ("blouse", "knitwear", "blouse"), ("top", "knitwear", "top"),
    ("dress", "knitwear", "dress"), ("robe", "knitwear", "dress"),
    ("skirt", "knitwear", "skirt"), ("jupe", "knitwear", "skirt"),
    ("gonna", "knitwear", "skirt"),
    # jewelry
    ("necklace", "jewelry", "necklace"), ("collier", "jewelry", "necklace"),
    ("earring", "jewelry", "earrings"), ("pendant", "jewelry", "pendant"),
    ("bracelet", "jewelry", "bracelet"), ("ring", "jewelry", "ring"),
    ("bague", "jewelry", "ring"), ("chain", "jewelry", "chain"),
    # eyewear
    ("sunglass", "eyewear", "sunglasses"), ("lunette", "eyewear", "sunglasses"),
    ("glasses", "eyewear", "sunglasses"), ("occhiali", "eyewear", "sunglasses"),
]


def detect_item_type(text: str) -> str | None:
    """Resolve a canonical English item-type from any-language listing text.

    Tries Russian fragments first (Oskelly), then English/European fragments
    (Vinted). Returns the canonical item-type phrase (e.g. "tote bag",
    "sneakers", "dress") or None when nothing recognisable is present.
    """
    if not text:
        return None
    lower = text.lower()
    for fragment, _cat, item_type in RUSSIAN_TO_ITEM_TYPE:
        if fragment in lower:
            return item_type
    for fragment, _cat, item_type in ENGLISH_TO_ITEM_TYPE:
        if fragment in lower:
            return item_type
    return None


# Canonical item-type -> coarse "bucket". Two listings in the same category but
# different buckets are almost certainly different products (a dress is not a
# t-shirt; a sneaker is not a boot). Synonyms collapse into one bucket so a
# generic "bag" still matches a "tote bag".
ITEM_TYPE_BUCKETS: dict[str, str] = {
    # shoes
    "sneakers": "sneakers", "boots": "boots", "heels": "heels",
    "loafers": "flats", "ballet flats": "flats", "mules": "flats",
    "sandals": "sandals", "espadrilles": "sandals", "shoes": "",  # generic: no gate
    # bags  (specific models are gated separately by model name)
    "bag": "bag", "tote bag": "bag", "belt bag": "bag", "briefcase": "bag",
    "backpack": "backpack", "clutch": "clutch", "wallet": "wallet",
    # outerwear
    "coat": "coat", "raincoat": "coat", "jacket": "jacket",
    "bomber jacket": "jacket", "down jacket": "jacket", "anorak": "jacket",
    "vest": "vest",
    # knitwear / tops
    "t-shirt": "top", "polo shirt": "top", "top": "top",
    "long sleeve": "top", "blouse": "top", "shirt": "shirt",
    "sweater": "knit", "pullover": "knit", "cardigan": "knit",
    "hoodie": "sweat", "sweatshirt": "sweat",
    "dress": "dress", "skirt": "skirt",
    # denim
    "jeans": "jeans", "trousers": "trousers", "shorts": "shorts",
    # jewelry
    "necklace": "necklace", "earrings": "earrings", "pendant": "necklace",
    "bracelet": "bracelet", "ring": "ring", "chain": "necklace",
    # eyewear
    "sunglasses": "sunglasses",
}


def item_types_conflict(type_a: str | None, type_b: str | None) -> bool:
    """True when both item-types are known and fall in different hard buckets.

    Generic types (empty bucket, e.g. plain "shoes"/"bag") never conflict.
    """
    if not type_a or not type_b:
        return False
    bucket_a = ITEM_TYPE_BUCKETS.get(type_a.lower())
    bucket_b = ITEM_TYPE_BUCKETS.get(type_b.lower())
    if not bucket_a or not bucket_b:
        return False
    return bucket_a != bucket_b


def resolve_semantics(
    brand: str,
    category: str,
    subcategory: str | None,
    title: str | None,
    description: str | None = None,
) -> tuple[str | None, str | None]:
    """Resolve (canonical_model, item_type) for a listing from stored fields.

    Language-independent: works on Russian (Oskelly) and EN/FR/IT/DE/NL
    (Vinted) text alike.

    1. Try the curated BRAND_MODELS registry over title + description +
       subcategory. A hit yields the canonical model name and its item type.
    2. Otherwise fall back to keyword-based item-type detection (model unknown).
    """
    from app.core.models_guide import find_model

    text = " ".join(p for p in (title, description, subcategory) if p)
    entry = find_model(brand, text)
    if entry:
        return entry["canonical"], entry.get("subcategory")

    item_type = detect_item_type(text)
    return None, item_type


def model_match_score(model_a: str | None, model_b: str | None) -> float | None:
    """Cross-language model agreement.

    100 when both sides resolve to the same canonical model, 0 when they resolve
    to different models, None when at least one side has no recognised model
    (signal unavailable — weight is redistributed by the caller).
    """
    if not model_a or not model_b:
        return None
    return 100.0 if model_a.strip().lower() == model_b.strip().lower() else 0.0


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
