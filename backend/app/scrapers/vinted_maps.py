"""Vinted category keywords and condition mapping."""

VINTED_CONDITION_MAP = {
    "new with tags": "new",
    "neuf avec étiquette": "new",
    "neuf avec etiquette": "new",
    "new without tags": "excellent",
    "neuf sans étiquette": "excellent",
    "neuf sans etiquette": "excellent",
    "very good": "excellent",
    "très bon état": "excellent",
    "tres bon etat": "excellent",
    "good": "good",
    "bon état": "good",
    "bon etat": "good",
    "satisfactory": "fair",
    "satisfaisant": "fair",
}

# Extra search terms per internal category (combined with brand name)
VINTED_CATEGORY_QUERIES: dict[str, list[str]] = {
    "bags": ["bag", "sac"],
    "shoes": ["shoes", "chaussures", "sneakers"],
    "outerwear": ["coat", "jacket", "manteau"],
    "denim": ["jeans", "denim"],
    "knitwear": ["sweater", "pull", "t-shirt"],
    "accessories": ["belt", "scarf", "accessoire"],
    "jewelry": ["jewelry", "necklace", "bijou"],
    "eyewear": ["sunglasses", "glasses", "lunettes"],
}

# Known Vinted brand IDs (fallback if API lookup fails)
VINTED_BRAND_IDS: dict[str, int] = {
    "prada": 3573,
    "miu miu": 999999,  # resolved via API
    "maison margiela": 999998,
    "balenciaga": 999997,
    "rick owens": 999996,
    "diesel": 999995,
    "acne studios": 999994,
    "chrome hearts": 999993,
    "saint laurent": 999992,
    "gucci": 999991,
    "bottega veneta": 999990,
    "comme des garçons": 999989,
}


def map_vinted_condition(status: str | None) -> str:
    if not status:
        return "good"
    return VINTED_CONDITION_MAP.get(status.lower().strip(), "good")


def infer_category_from_title(title: str, default: str = "accessories") -> str:
    lower = title.lower()
    rules = [
        # shoes — EN/FR/IT/DE/NL
        (["sneaker", "shoe", "boot", "chaussure", "talons", "tabi",
          "scarpa", "scarpe", "stiefel", "schuh", "schoenen",
          "loafer", "mocassin", "mocassino", "sandale", "sandal",
          "heel", "pump", "flat", "ballerina", "espadrille", "mule",
          "slip-on", "slipon", "sabot", "ciabatta", "schuhe",
          "sandl", "sandles", "wedge", "derby",
          "runner", "trainer", "sneaker", "basketball shoe"], "shoes"),
        # bags — EN/FR/IT/DE/NL
        (["bag", "sac", "pochette", "bolso", "borsa", "borsellino",
          "tasche", "handtas", "clutch", "tote", "backpack", "wallet",
          "purse", "porte-monnaie", "portafoglio", "portemonnaie"], "bags"),
        # denim
        (["jean", "denim", "jeans", "pantalon", "broek"], "denim"),
        # outerwear — EN/FR/IT/DE/NL
        (["coat", "jacket", "blouson", "manteau", "veste", "jas",
          "giaccone", "cappotto", "jacke", "parka", "bomber", "vest"], "outerwear"),
        # knitwear / tops — EN/FR/IT/DE/NL
        (["sweater", "pull", "shirt", "tee", "top", "hoodie",
          "sweatshirt", "cardigan", "polo", "maglia", "maglione",
          "bluse", "dress", "robe", "gonna", "skirt", "longsleeve",
          "trui", "jurk", "rok"], "knitwear"),
        # jewelry
        (["necklace", "ring", "jewel", "pendant", "bracelet",
          "earring", "collier", "bague", "bijou"], "jewelry"),
        # eyewear — EN/FR/IT/DE/NL
        (["sunglass", "glasses", "lunettes", "occhiali", "brille",
          "bril", "montuur", "eyewear", "sunglasses"], "eyewear"),
    ]
    for keywords, cat in rules:
        if any(k in lower for k in keywords):
            return cat
    return default
