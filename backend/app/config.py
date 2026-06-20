from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{DATA_DIR.as_posix()}/lux_arbitrage.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(ROOT_DIR / ".env.local")),
        extra="ignore",
    )

    app_env: str = "development"
    secret_key: str = "dev-secret-change-in-production"
    api_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str = DEFAULT_SQLITE_URL
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    meilisearch_url: str = "http://localhost:7700"
    meilisearch_master_key: str = "masterKey"
    meilisearch_enabled: bool = False

    exchange_rate_api: str = "https://api.frankfurter.app/latest"
    match_confidence_threshold: float = 50.0
    opportunity_min_roi: float = 0.15

    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    vinted_enabled: bool = True
    oskelly_enabled: bool = True
    scraper_interval_minutes: int = 60
    scraper_listings_per_query: int = 20
    scraper_stale_hours: int = 72

    # Vercel proxy URL — the backend fetches Vinted data via the Next.js
    # /api/vinted route running from a European edge region (fra1), bypassing
    # Vinted's DataDome block on Render's US servers.
    # Override with VINTED_PROXY_URL env var if the Vercel domain changes.
    vinted_proxy_url: str = "https://lux-arbitrage.vercel.app"

    vinted_domain: str = "fr"
    vinted_per_page: int = 48
    vinted_max_pages: int = 2
    vinted_min_price_eur: int = 40

    oskelly_base_url: str = "https://oskelly.ru"
    oskelly_max_pages: int = 2
    oskelly_min_price_rub: int = 5000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
