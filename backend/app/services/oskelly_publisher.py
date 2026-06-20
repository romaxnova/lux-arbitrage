"""Adapt a source (Vinted) listing into an original Russian Oskelly listing.

Two concerns live here:

1. `build_russian_listing` — pure, fully testable. Generates an *adapted*
   Russian title + description from structured fields. It deliberately does NOT
   copy the original seller's free text; it composes fresh marketing copy from
   the brand, model, item type, condition and size so each posting is original.

2. `OskellyPublisher` — the authenticated client that would create the draft on
   Oskelly. It is guarded: credentials come from env, and publishing only
   happens when explicitly enabled. By default the endpoint runs in preview
   ("dry-run") mode and never touches the live account.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


# English canonical item type -> Russian noun (nominative). Mirrors the
# item-type vocabulary produced by normalization.detect_item_type.
ITEM_TYPE_RU: dict[str, str] = {
    # bags
    "bag": "Сумка", "tote bag": "Сумка-тоут", "shopper bag": "Сумка-шоппер",
    "belt bag": "Поясная сумка", "backpack": "Рюкзак", "clutch": "Клатч",
    "wallet": "Кошелёк", "briefcase": "Портфель",
    # shoes
    "sneakers": "Кроссовки", "boots": "Ботинки", "heels": "Туфли",
    "loafers": "Лоферы", "ballet flats": "Балетки", "mules": "Мюли",
    "sandals": "Босоножки", "espadrilles": "Эспадрильи", "shoes": "Обувь",
    # outerwear
    "coat": "Пальто", "jacket": "Куртка", "bomber jacket": "Бомбер",
    "down jacket": "Пуховик", "anorak": "Анорак", "raincoat": "Плащ",
    "vest": "Жилет",
    # knitwear / tops
    "t-shirt": "Футболка", "polo shirt": "Поло", "top": "Топ",
    "blouse": "Блуза", "shirt": "Рубашка", "sweater": "Свитер",
    "pullover": "Пуловер", "cardigan": "Кардиган", "hoodie": "Худи",
    "sweatshirt": "Свитшот", "dress": "Платье", "skirt": "Юбка",
    "long sleeve": "Лонгслив",
    # denim
    "jeans": "Джинсы", "trousers": "Брюки", "shorts": "Шорты",
    # jewelry
    "necklace": "Колье", "earrings": "Серьги", "pendant": "Кулон",
    "bracelet": "Браслет", "ring": "Кольцо", "chain": "Цепочка",
    # eyewear
    "sunglasses": "Солнцезащитные очки",
}

# Internal condition code -> Russian phrasing (Oskelly-style).
CONDITION_RU: dict[str, str] = {
    "new": "Новое с биркой",
    "excellent": "Отличное состояние",
    "good": "Хорошее состояние",
    "fair": "Удовлетворительное состояние",
}

# Default category genitive for the closing line ("привезено под заказ").
CATEGORY_RU: dict[str, str] = {
    "bags": "сумок",
    "shoes": "обуви",
    "outerwear": "верхней одежды",
    "denim": "денима",
    "knitwear": "одежды",
    "accessories": "аксессуаров",
    "jewelry": "украшений",
    "eyewear": "очков",
}


@dataclass
class RussianListing:
    title: str
    description: str
    brand: str
    item_type_ru: str
    condition_ru: str
    size: str | None
    price_rub: int
    category: str
    images: list[str]


def _ru_type(item_type: str | None, category: str) -> str:
    if item_type and item_type.lower() in ITEM_TYPE_RU:
        return ITEM_TYPE_RU[item_type.lower()]
    # Fall back to a sensible category noun
    return {
        "bags": "Сумка", "shoes": "Обувь", "outerwear": "Верхняя одежда",
        "denim": "Джинсы", "knitwear": "Одежда", "accessories": "Аксессуар",
        "jewelry": "Украшение", "eyewear": "Очки",
    }.get(category, "Изделие")


def build_russian_listing(
    *,
    brand: str,
    model: str | None,
    item_type: str | None,
    category: str,
    condition: str,
    size: str | None,
    price_rub: float | int,
    images: list[str] | None = None,
) -> RussianListing:
    """Compose an original Russian Oskelly listing from structured fields.

    The text is generated, not copied: a clean title plus a structured
    description with condition, size, authenticity and delivery copy in Russian.
    """
    ru_type = _ru_type(item_type, category)
    condition_ru = CONDITION_RU.get(condition, "Хорошее состояние")

    # Title: "<Тип> <Brand> <Model>" — Oskelly's house style. Model (Latin) is
    # kept as-is because luxury model names are not translated in RU listings.
    parts = [ru_type, brand]
    if model:
        # Drop a trailing generic word ("Bag"/"Sneakers") from the model since
        # the Russian type already conveys it.
        model_clean = model
        for tail in (" Bag", " Sneakers", " Boots", " Shoes"):
            if model_clean.endswith(tail):
                model_clean = model_clean[: -len(tail)]
        parts.append(model_clean.strip())
    title = " ".join(p for p in parts if p).strip()

    price_int = int(round(float(price_rub)))

    lines = [
        f"{brand} — оригинал. {ru_type.lower()} из новой коллекции, привезено из Европы.",
        "",
        f"• Бренд: {brand}",
    ]
    if model:
        lines.append(f"• Модель: {model}")
    lines.append(f"• Состояние: {condition_ru}")
    if size:
        lines.append(f"• Размер: {size}")
    lines.append("• Подлинность: гарантирована, проходит проверку Oskelly.")
    lines.append("")
    lines.append(
        f"Привезено из Европы под заказ — большой выбор {CATEGORY_RU.get(category, 'товаров')} "
        "люксовых брендов. Быстрая доставка по России, возможен торг. "
        "Пишите — отвечу на все вопросы и пришлю дополнительные фото."
    )
    description = "\n".join(lines)

    return RussianListing(
        title=title,
        description=description,
        brand=brand,
        item_type_ru=ru_type,
        condition_ru=condition_ru,
        size=size,
        price_rub=price_int,
        category=category,
        images=images or [],
    )


class OskellyPublisher:
    """Authenticated Oskelly client for creating listing drafts.

    Guarded by design:
      * credentials are read from env (OSKELLY_LOGIN / OSKELLY_PASSWORD),
      * `publish()` refuses to post unless OSKELLY_PUBLISH_ENABLED is true,
      * the actual create-draft endpoint must be confirmed before going live;
        until then `publish()` returns a structured `needs_configuration`
        result rather than blindly POSTing to the production account.
    """

    LOGIN_URL = "https://oskelly.ru/api/auth/login"
    DRAFT_URL = "https://oskelly.ru/api/v2/products"

    def __init__(self) -> None:
        s = get_settings()
        self.login = s.oskelly_login
        self.password = s.oskelly_password
        self.enabled = s.oskelly_publish_enabled
        self.base_url = s.oskelly_base_url.rstrip("/")
        self._token: str | None = None

    def is_configured(self) -> bool:
        return bool(self.login and self.password)

    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        if not self.is_configured():
            return False
        try:
            resp = await client.post(
                self.LOGIN_URL,
                json={"email": self.login, "password": self.password},
                headers={"Accept": "application/json", "Accept-Language": "ru-RU"},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Oskelly auth request failed: %s", exc)
            return False
        if resp.status_code != 200:
            logger.warning("Oskelly auth returned %s", resp.status_code)
            return False
        data = resp.json()
        self._token = data.get("token") or data.get("access_token")
        return bool(self._token)

    async def publish(self, listing: RussianListing) -> dict:
        """Attempt to create a draft on Oskelly.

        Returns a structured result. Never raises on expected failure paths so
        the API endpoint can surface a clean status to the UI.
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Публикация отключена. Установите OSKELLY_PUBLISH_ENABLED=true.",
            }
        if not self.is_configured():
            return {
                "status": "needs_configuration",
                "message": "Не заданы OSKELLY_LOGIN / OSKELLY_PASSWORD.",
            }

        async with httpx.AsyncClient(timeout=30) as client:
            if not await self.authenticate(client):
                return {"status": "auth_failed", "message": "Не удалось авторизоваться на Oskelly."}

            # The create-draft contract (category/brand IDs, image upload tokens)
            # must be confirmed against the live account before enabling real
            # posts. Until then we stop here with a clear, actionable status
            # instead of POSTing an unverified payload to production.
            return {
                "status": "draft_ready",
                "message": (
                    "Авторизация успешна. Карточка подготовлена к публикации; "
                    "перед автопостингом необходимо сопоставить ID категории/бренда "
                    "и загрузку изображений Oskelly."
                ),
                "payload": {
                    "name": listing.title,
                    "description": listing.description,
                    "price": listing.price_rub,
                    "brand": listing.brand,
                    "condition": listing.condition_ru,
                    "size": listing.size,
                    "images": listing.images,
                },
            }


def listing_to_dict(listing: RussianListing) -> dict:
    return asdict(listing)
