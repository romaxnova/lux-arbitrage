BRAND_ALIASES: dict[str, list[str]] = {
    "Saint Laurent": ["YSL", "Yves Saint Laurent", "Saint Laurent Paris"],
    "Maison Margiela": ["Margiela", "MM6", "MM6 Maison Margiela"],
    "Comme des Garçons": ["CDG", "Comme des Garcons", "Comme Des Garcons"],
    "Miu Miu": ["MIU MIU"],
    "Acne Studios": ["Acne", "ACNE Studios"],
    "Rick Owens": ["Rick Owens DRKSHDW", "DRKSHDW"],
    "Chrome Hearts": ["CH"],
    "Bottega Veneta": ["BV"],
    "Alexander McQueen": ["McQueen"],
    "Off-White": ["Off White", "OFF WHITE"],
    "Vetements": ["VETEMENTS"],
    "Prada": [],
    "Balenciaga": [],
    "Diesel": [],
    "Gucci": [],
    "Loewe": [],
    "Jacquemus": [],
    "The Row": [],
    "Celine": ["Céline"],
}

PRIORITY_BRANDS = [
    "Prada",
    "Miu Miu",
    "Maison Margiela",
    "Balenciaga",
    "Rick Owens",
    "Diesel",
    "Acne Studios",
    "Chrome Hearts",
    "Saint Laurent",
    "Gucci",
    "Bottega Veneta",
    "Comme des Garçons",
]

CATEGORIES = ["bags", "shoes", "outerwear", "denim", "knitwear", "accessories", "jewelry", "eyewear"]

CONDITION_MAP = {
    "new": "new",
    "new with tags": "new",
    "brand new": "new",
    "excellent": "excellent",
    "very good": "excellent",
    "like new": "excellent",
    "good": "good",
    "satisfactory": "fair",
    "fair": "fair",
}

# Clothing sizes: system -> EU
CLOTHING_SIZE_MAP = {
    "US": {"XS": "34", "S": "36", "M": "38", "L": "40", "XL": "42", "XXL": "44"},
    "UK": {"6": "34", "8": "36", "10": "38", "12": "40", "14": "42", "16": "44"},
    "IT": {"38": "34", "40": "36", "42": "38", "44": "40", "46": "42", "48": "44"},
    "EU": {"34": "34", "36": "36", "38": "38", "40": "40", "42": "42", "44": "44"},
}

# Shoe sizes: approximate US/UK -> EU
SHOE_SIZE_MAP = {
    "US": {"6": "37", "7": "38", "8": "39", "9": "40", "10": "41", "11": "42", "12": "43"},
    "UK": {"5": "38", "6": "39", "7": "40", "8": "41", "9": "42", "10": "43"},
    "EU": {str(i): str(i) for i in range(35, 46)},
}

NOISE_WORDS = {
    "authentic", "original", "genuine", "rare", "vintage", "luxury", "designer",
    "sale", "new", "used", "preloved", "pre-loved", "wow", "must", "see",
}

SCORING_WEIGHTS = {
    "roi": 0.35,
    "demand": 0.25,
    "liquidity": 0.20,
    "price_gap": 0.20,
    "risk": 0.15,
}

MATCH_WEIGHTS = {
    "brand": 0.25,
    "title": 0.25,
    "image": 0.20,
    "category": 0.15,
    "size": 0.15,
}
