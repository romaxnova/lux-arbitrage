"""Oskelly Nuxt 3 payload helpers."""

from __future__ import annotations

import json
import re
from typing import Any


def resolve_ref(payload: list[Any], val: Any, max_hops: int = 40) -> Any:
    seen: set[int] = set()
    for _ in range(max_hops):
        if isinstance(val, int) and 0 <= val < len(payload):
            if val in seen:
                break
            seen.add(val)
            val = payload[val]
        else:
            break
    return val


def _resolve_brand(payload: list[Any], brand_ref: Any) -> str:
    brand = resolve_ref(payload, brand_ref)
    if isinstance(brand, dict):
        name = resolve_ref(payload, brand.get("name"))
        if isinstance(name, str):
            return name
        title = resolve_ref(payload, brand.get("title"))
        if isinstance(title, str):
            return title
    return "Unknown"


def _resolve_category(payload: list[Any], category_ref: Any) -> tuple[str, str | None]:
    category = resolve_ref(payload, category_ref)
    if not isinstance(category, dict):
        return "accessories", None
    display = resolve_ref(payload, category.get("displayName") or category.get("fullName"))
    singular = resolve_ref(payload, category.get("singularName"))
    name = display if isinstance(display, str) else (singular if isinstance(singular, str) else "accessories")
    return map_oskelly_category(name), name


def _upgrade_image_url(url: str) -> str:
    """Oskelly CDN stores thumbnails as 'tiny-UUID' and full images as 'item-UUID'.
    Replace the tiny prefix so the card shows a usable full-size photo."""
    if "/tiny-" in url:
        return url.replace("/tiny-", "/item-")
    return url


def _resolve_images(payload: list[Any], images_ref: Any) -> list[str]:
    images = resolve_ref(payload, images_ref)
    if isinstance(images, int):
        images = resolve_ref(payload, images)
    if not isinstance(images, list):
        return []
    urls: list[str] = []
    for img_ref in images[:8]:
        img = resolve_ref(payload, img_ref)
        if isinstance(img, dict):
            for key in ("path", "url", "imageUrl", "src"):
                val = resolve_ref(payload, img.get(key))
                if isinstance(val, str) and val.startswith("http"):
                    urls.append(_upgrade_image_url(val))
                    break
            else:
                path = resolve_ref(payload, img.get("path"))
                if isinstance(path, str) and path.startswith("http"):
                    urls.append(_upgrade_image_url(path))
        elif isinstance(img, str) and img.startswith("http"):
            urls.append(_upgrade_image_url(img))
    return urls


def _resolve_sizes(payload: list[Any], sizes_ref: Any) -> str | None:
    sizes = resolve_ref(payload, sizes_ref)
    if not isinstance(sizes, list) or not sizes:
        return None
    first = resolve_ref(payload, sizes[0])
    if isinstance(first, dict):
        for key in ("value", "name", "sizeValue", "displayName"):
            val = resolve_ref(payload, first.get(key))
            if isinstance(val, str):
                return val
    return None


OSKELLY_CATEGORY_MAP = {
    "сумк": "bags",
    "рюкзак": "bags",
    "клатч": "bags",
    "кошел": "bags",
    "обув": "shoes",
    "ботин": "shoes",
    "кроссов": "shoes",
    "кед": "shoes",
    "сапог": "shoes",
    "туфл": "shoes",
    "балет": "shoes",
    "джинс": "denim",
    "брюк": "denim",
    "пальт": "outerwear",
    "куртк": "outerwear",
    "пухов": "outerwear",
    "плать": "knitwear",
    "футбол": "knitwear",
    "рубаш": "knitwear",
    "свитер": "knitwear",
    "колье": "jewelry",
    "серьг": "jewelry",
    "кулон": "jewelry",
    "браслет": "jewelry",
    "очк": "eyewear",
    "ремен": "accessories",
    "шарф": "accessories",
    "перчат": "accessories",
}


def map_oskelly_category(name: str) -> str:
    lower = name.lower()
    for prefix, cat in OSKELLY_CATEGORY_MAP.items():
        if prefix in lower:
            return cat
    return "accessories"


OSKELLY_CONDITION_MAP = {
    "новое с биркой": "new",
    "отличное состояние": "excellent",
    "хорошее состояние": "good",
    "удовлетворительное": "fair",
}


def map_oskelly_condition(name: str | None) -> str:
    if not name:
        return "good"
    return OSKELLY_CONDITION_MAP.get(name.lower().strip(), "good")


def extract_nuxt_payload(html: str) -> list[Any]:
    scripts = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not scripts:
        raise ValueError("Oskelly Nuxt payload not found")
    return json.loads(scripts[0])


def extract_product_urls(html: str) -> dict[int, str]:
    """Map productId -> canonical product path from anchor tags."""
    mapping: dict[int, str] = {}
    for path in re.findall(r'href="(/products/[^"]+)"', html):
        m = re.search(r"-(\d+)$", path)
        if m:
            mapping[int(m.group(1))] = f"https://oskelly.ru{path}"
    return mapping


def parse_product_record(
    payload: list[Any], raw: dict[str, Any], url_map: dict[int, str], product_id: int
) -> dict[str, Any] | None:
    name = resolve_ref(payload, raw.get("name"))
    if not isinstance(name, str):
        return None

    brand_name = _resolve_brand(payload, raw.get("brand"))
    category, subcategory = _resolve_category(payload, raw.get("category"))
    price = resolve_ref(payload, raw.get("price"))
    if not isinstance(price, (int, float)):
        price = resolve_ref(payload, raw.get("prettyPrice"))
    condition_name = resolve_ref(payload, raw.get("conditionName"))
    state = resolve_ref(payload, raw.get("productState"))
    description = resolve_ref(payload, raw.get("description"))
    images = _resolve_images(payload, raw.get("images"))
    size = _resolve_sizes(payload, raw.get("sizes"))

    is_sold = state in ("SOLD", "SOLD_OUT", "ARCHIVED", "DELETED")

    return {
        "external_id": str(product_id),
        "brand": brand_name,
        "title": f"{brand_name} {name}".strip(),
        "category": category,
        "subcategory": subcategory,
        "size_raw": size,
        "size_system": "EU",
        "condition": map_oskelly_condition(condition_name if isinstance(condition_name, str) else None),
        "price": price,
        "currency": "RUB",
        "seller_country": "RU",
        "listing_url": url_map.get(product_id, f"https://oskelly.ru/product/{product_id}"),
        "image_urls": images,
        "description": description if isinstance(description, str) else "",
        "is_sold": is_sold,
    }


def extract_products_from_catalog(html: str) -> list[dict[str, Any]]:
    payload = extract_nuxt_payload(html)
    url_map = extract_product_urls(html)
    products: list[dict[str, Any]] = []
    seen: set[int] = set()

    for item in payload:
        if not isinstance(item, dict):
            continue
        if "name" not in item or "brand" not in item:
            continue
        if "price" not in item and "prettyPrice" not in item:
            continue

        resolved_id = resolve_ref(payload, item.get("productId"))
        if not isinstance(resolved_id, int) or resolved_id < 10000:
            continue
        if resolved_id in seen:
            continue
        seen.add(resolved_id)

        record = parse_product_record(payload, item, url_map, resolved_id)
        if record and record.get("price"):
            products.append(record)

    return products
