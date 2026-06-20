"""
Comprehensive model registry for luxury brands.

Each model entry defines:
  canonical: official model name
  aliases: lower-case strings that, if found in a listing title/description,
           identify this model (multilingual: EN/FR/IT/DE/RU)
  search_en: the English phrase to use when querying Vinted
  category: the item category this model belongs to
  subcategory: specific item type (maps to extract_item_type output)

Only listings with a recognised model should be matched — everything
else is unverifiable noise.
"""

from __future__ import annotations

# (brand_canonical, [ModelEntry...])
# ModelEntry = dict with keys: canonical, aliases, search_en, category, subcategory
BRAND_MODELS: dict[str, list[dict]] = {

    "Prada": [
        # Bags
        {"canonical": "Re-Edition 2000", "aliases": ["re-edition 2000", "re edition 2000", "reedition 2000", "re-edition2000"], "search_en": "Re-Edition 2000", "category": "bags", "subcategory": "bag"},
        {"canonical": "Re-Edition 2005", "aliases": ["re-edition 2005", "re edition 2005", "reedition 2005"], "search_en": "Re-Edition 2005", "category": "bags", "subcategory": "bag"},
        {"canonical": "Re-Edition 1978", "aliases": ["re-edition 1978", "re edition 1978"], "search_en": "Re-Edition 1978", "category": "bags", "subcategory": "bag"},
        {"canonical": "Galleria", "aliases": ["galleria"], "search_en": "Galleria bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Cleo", "aliases": ["cleo"], "search_en": "Cleo bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Cahier", "aliases": ["cahier"], "search_en": "Cahier bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Re-Nylon Backpack", "aliases": ["re-nylon", "re nylon backpack"], "search_en": "Re-Nylon backpack", "category": "bags", "subcategory": "backpack"},
        {"canonical": "Triangle Bag", "aliases": ["triangle bag", "triangolo"], "search_en": "Triangle bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Panier", "aliases": ["panier"], "search_en": "Panier bag", "category": "bags", "subcategory": "bag"},
        # Shoes
        {"canonical": "Monolith Boots", "aliases": ["monolith", "monolith boots", "monolith loafers", "monolith pump"], "search_en": "Monolith", "category": "shoes", "subcategory": "boots"},
        {"canonical": "Cloudbust Thunder", "aliases": ["cloudbust thunder", "cloudbust", "cloud bust"], "search_en": "Cloudbust Thunder sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "America's Cup Sneakers", "aliases": ["america's cup", "americas cup"], "search_en": "America's Cup sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Slingback Pumps", "aliases": ["slingback", "sling back pump"], "search_en": "slingback pumps", "category": "shoes", "subcategory": "heels"},
    ],

    "Miu Miu": [
        {"canonical": "Wander Bag", "aliases": ["wander", "wander bag", "wander mini"], "search_en": "Wander bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Arcadie Bag", "aliases": ["arcadie"], "search_en": "Arcadie bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Aventure Bag", "aliases": ["aventure"], "search_en": "Aventure bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Ivy Bag", "aliases": ["ivy bag", "ivy mini"], "search_en": "Ivy bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Pocket Bag", "aliases": ["pocket bag", "pocket matelassé", "pocket matelasse"], "search_en": "Pocket bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Ballet Flats", "aliases": ["ballerine", "ballet flat", "ballerina", "балетки miu miu"], "search_en": "ballet flats", "category": "shoes", "subcategory": "ballet flats"},
        {"canonical": "Mini Skirt", "aliases": ["mini skirt", "minigonna", "юбка мини miu miu", "mini jupe"], "search_en": "mini skirt", "category": "knitwear", "subcategory": "skirt"},
    ],

    "Bottega Veneta": [
        {"canonical": "Jodie Bag", "aliases": ["jodie", "jodie mini", "jodie small", "jodie large", "mini jodie"], "search_en": "Jodie bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Cassette Bag", "aliases": ["cassette", "cassette bag", "cassette mini", "padded cassette"], "search_en": "Cassette bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Andiamo Bag", "aliases": ["andiamo", "andiamo large", "andiamo tote"], "search_en": "Andiamo bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Gemelli Bag", "aliases": ["gemelli"], "search_en": "Gemelli bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Intrecciato Pouch", "aliases": ["pouch", "intrecciato pouch", "clutch intrecciato"], "search_en": "Intrecciato pouch", "category": "bags", "subcategory": "clutch"},
        {"canonical": "Concert Pouch", "aliases": ["concert pouch", "concert bag"], "search_en": "Concert pouch", "category": "bags", "subcategory": "clutch"},
        {"canonical": "Point Shoes", "aliases": ["point boot", "point mule", "point ankle"], "search_en": "Point boots", "category": "shoes", "subcategory": "boots"},
        {"canonical": "BV Tire Shoes", "aliases": ["bv tire", "tire boot", "tire mule"], "search_en": "BV Tire", "category": "shoes", "subcategory": "boots"},
        {"canonical": "Stretch Mules", "aliases": ["stretch mule", "stretch sandal"], "search_en": "stretch mules", "category": "shoes", "subcategory": "mules"},
    ],

    "Saint Laurent": [
        {"canonical": "Loulou Bag", "aliases": ["loulou", "lou lou"], "search_en": "Loulou bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Sac de Jour", "aliases": ["sac de jour", "sac de jour nano"], "search_en": "Sac de Jour", "category": "bags", "subcategory": "bag"},
        {"canonical": "Kate Bag", "aliases": ["kate bag", "kate clutch", "kate monogram"], "search_en": "Kate bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Jamie Bag", "aliases": ["jamie", "jamie 4.3", "jamie bag"], "search_en": "Jamie bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Le 5 à 7 Bag", "aliases": ["le 5 a 7", "le 5 à 7", "5 a 7", "cinq a sept"], "search_en": "Le 5 à 7 bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Sunset Bag", "aliases": ["sunset", "sunset bag", "sunset medium"], "search_en": "Sunset bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Rive Gauche Tote", "aliases": ["rive gauche", "rive gauche tote"], "search_en": "Rive Gauche tote", "category": "bags", "subcategory": "bag"},
        {"canonical": "Cassandra Bag", "aliases": ["cassandra", "cassandre"], "search_en": "Cassandra bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Le Loafer", "aliases": ["le loafer", "loafer ysl", "monogram loafer"], "search_en": "Le Loafer", "category": "shoes", "subcategory": "loafers"},
        {"canonical": "Tribute Heels", "aliases": ["tribute", "tribute platform", "tribute mule"], "search_en": "Tribute heels", "category": "shoes", "subcategory": "heels"},
        {"canonical": "Cassandra Pumps", "aliases": ["cassandra pump", "cassandra heel"], "search_en": "Cassandra pumps", "category": "shoes", "subcategory": "heels"},
        {"canonical": "Wyatt Boots", "aliases": ["wyatt", "wyatt boot", "wyatt harness"], "search_en": "Wyatt boots", "category": "shoes", "subcategory": "boots"},
    ],

    "Gucci": [
        {"canonical": "Horsebit 1955", "aliases": ["horsebit 1955", "horsebit 1961", "horsebit bag"], "search_en": "Horsebit 1955 bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "GG Marmont", "aliases": ["gg marmont", "marmont", "marmont mini", "marmont matelasse"], "search_en": "GG Marmont bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Dionysus", "aliases": ["dionysus", "dionysus mini", "dionysus small"], "search_en": "Dionysus bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Jackie 1961", "aliases": ["jackie 1961", "jackie bag", "jackie"], "search_en": "Jackie 1961 bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Ophidia", "aliases": ["ophidia", "ophidia gg", "ophidia mini", "ophidia medium"], "search_en": "Ophidia bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Bamboo", "aliases": ["bamboo bag", "bamboo 1947", "bamboo mini"], "search_en": "Bamboo bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Ace Sneakers", "aliases": ["ace sneaker", "ace shoe"], "search_en": "Ace sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Rhyton Sneakers", "aliases": ["rhyton"], "search_en": "Rhyton sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Flashtrek Sneakers", "aliases": ["flashtrek", "flash trek"], "search_en": "Flashtrek sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Princetown Loafers", "aliases": ["princetown", "prince town"], "search_en": "Princetown loafers", "category": "shoes", "subcategory": "loafers"},
        {"canonical": "Horsebit Loafers", "aliases": ["horsebit loafer", "horsebit mule", "horsebit pump"], "search_en": "Horsebit loafers", "category": "shoes", "subcategory": "loafers"},
    ],

    "Balenciaga": [
        {"canonical": "Triple S", "aliases": ["triple s", "triple-s"], "search_en": "Triple S sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Speed Trainer", "aliases": ["speed trainer", "speed sock", "speed stretch"], "search_en": "Speed Trainer", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Track Sneakers", "aliases": ["track sneaker", "balenciaga track"], "search_en": "Track sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "10XL Sneakers", "aliases": ["10xl", "10 xl"], "search_en": "10XL sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "3XL Sneakers", "aliases": ["3xl", "3 xl"], "search_en": "3XL sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Le Cagole Bag", "aliases": ["le cagole", "cagole", "cagole xs", "cagole small", "cagole medium"], "search_en": "Le Cagole bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Hourglass Bag", "aliases": ["hourglass", "hourglass xs", "hourglass small", "hourglass tote"], "search_en": "Hourglass bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "City Bag", "aliases": ["city bag", "classic city", "motorcycle bag"], "search_en": "City bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Neo Classic", "aliases": ["neo classic", "neoclassic", "neo classic mini"], "search_en": "Neo Classic bag", "category": "bags", "subcategory": "bag"},
    ],

    "Maison Margiela": [
        {"canonical": "Tabi Boots", "aliases": ["tabi boot", "tabi ankle", "tabi split"], "search_en": "Tabi boots", "category": "shoes", "subcategory": "boots"},
        {"canonical": "Tabi Ballet Flats", "aliases": ["tabi flat", "tabi ballerina", "tabi mary jane"], "search_en": "Tabi flats", "category": "shoes", "subcategory": "ballet flats"},
        {"canonical": "Tabi Heels", "aliases": ["tabi pump", "tabi heel", "tabi stiletto"], "search_en": "Tabi heels", "category": "shoes", "subcategory": "heels"},
        {"canonical": "Replica Sneakers", "aliases": ["replica sneaker", "replica trainer", "replica low", "replica high", "evolution"], "search_en": "Replica sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Glam Slam Bag", "aliases": ["glam slam", "glam slam flap"], "search_en": "Glam Slam bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "5AC Bag", "aliases": ["5ac", "5 ac bag", "5ac small", "5ac medium"], "search_en": "5AC bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Classique Bag", "aliases": ["classique", "classique bag", "top handle classique"], "search_en": "Classique bag", "category": "bags", "subcategory": "bag"},
    ],

    "Rick Owens": [
        {"canonical": "Ramones Sneakers", "aliases": ["ramones", "ramones low", "ramones high", "ramones boot"], "search_en": "Ramones sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Geobasket Sneakers", "aliases": ["geobasket", "geo basket"], "search_en": "Geobasket sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Bozo Sneakers", "aliases": ["bozo", "bozo tractor"], "search_en": "Bozo sneakers", "category": "shoes", "subcategory": "sneakers"},
        {"canonical": "Rick Owens x Converse", "aliases": ["converse", "turbodrk", "turbo drk", "converse turbodrk"], "search_en": "Rick Owens Converse", "category": "shoes", "subcategory": "sneakers"},
    ],

    "Acne Studios": [
        {"canonical": "Musubi Bag", "aliases": ["musubi", "musubi micro", "musubi mini", "musubi midi"], "search_en": "Musubi bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Multipocket Bag", "aliases": ["multipocket", "multi pocket"], "search_en": "Multipocket bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "Papier Bag", "aliases": ["papier", "papier bag", "papier a4"], "search_en": "Papier bag", "category": "bags", "subcategory": "bag"},
    ],

    "Chrome Hearts": [
        {"canonical": "Plus Cross Ring", "aliases": ["plus cross ring", "cross ring", "sterling ring", "cemetery ring"], "search_en": "Cross ring", "category": "jewelry", "subcategory": "ring"},
        {"canonical": "Cross Patch Bracelet", "aliases": ["cross patch bracelet", "leather bracelet", "cross bracelet"], "search_en": "bracelet", "category": "jewelry", "subcategory": "bracelet"},
        {"canonical": "Cemetery Cross Necklace", "aliases": ["cemetery cross", "cross necklace", "cemetery necklace"], "search_en": "Cross necklace", "category": "jewelry", "subcategory": "necklace"},
        {"canonical": "Horse Shoe T-Shirt", "aliases": ["horse shoe", "horseshoe", "horse shoe logo"], "search_en": "Horse Shoe t-shirt", "category": "knitwear", "subcategory": "t-shirt"},
        {"canonical": "Logo Hoodie", "aliases": ["chrome hearts hoodie", "cross hoodie", "ch hoodie"], "search_en": "Chrome Hearts hoodie", "category": "knitwear", "subcategory": "hoodie"},
    ],

    "Comme des Garçons": [
        {"canonical": "PLAY Heart T-Shirt", "aliases": ["heart t-shirt", "play t-shirt", "play tee", "cdg play", "heart patch"], "search_en": "PLAY heart t-shirt", "category": "knitwear", "subcategory": "t-shirt"},
        {"canonical": "PLAY Hoodie", "aliases": ["play hoodie", "cdg hoodie", "heart hoodie"], "search_en": "PLAY hoodie", "category": "knitwear", "subcategory": "hoodie"},
    ],

    "Diesel": [
        {"canonical": "1DR Bag", "aliases": ["1dr", "1 dr bag", "diesel 1dr"], "search_en": "1DR bag", "category": "bags", "subcategory": "bag"},
        {"canonical": "D-Vina Jeans", "aliases": ["d-vina", "dvina"], "search_en": "D-Vina jeans", "category": "denim", "subcategory": "jeans"},
        {"canonical": "1969 D-Ebbey Jeans", "aliases": ["d-ebbey", "1969 d ebbey", "debbey"], "search_en": "D-Ebbey jeans", "category": "denim", "subcategory": "jeans"},
        {"canonical": "2019 D-Strukt Jeans", "aliases": ["d-strukt", "strukt", "2019 d strukt"], "search_en": "D-Strukt jeans", "category": "denim", "subcategory": "jeans"},
        {"canonical": "1995 D-Sirtuck Jeans", "aliases": ["d-sirtuck", "sirtuck"], "search_en": "D-Sirtuck jeans", "category": "denim", "subcategory": "jeans"},
    ],
}


def find_model(brand: str, text: str) -> dict | None:
    """Return the first matching model entry for a brand given any listing text.

    Checks *all* aliases case-insensitively against the combined title +
    description text. Returns the ModelEntry dict or None.
    """
    text_lower = text.lower()
    models = BRAND_MODELS.get(brand, [])
    for entry in models:
        if any(alias in text_lower for alias in entry["aliases"]):
            return entry
    return None
