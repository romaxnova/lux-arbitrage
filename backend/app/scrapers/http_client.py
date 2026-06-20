"""Shared HTTP client with rate limiting and retries for marketplace scrapers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
}


class RateLimitedClient:
    def __init__(
        self,
        *,
        requests_per_second: float = 1.0,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._min_interval = 1.0 / requests_per_second
        self._last_request = 0.0
        self._lock = asyncio.Lock()
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> RateLimitedClient:
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=self._timeout,
            headers=DEFAULT_HEADERS,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _throttle(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait = self._min_interval - (now - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = loop.time()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None
        headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}

        for attempt in range(self._max_retries):
            await self._throttle()
            try:
                response = await self._client.get(url, headers=headers, **kwargs)
                if response.status_code in (429, 503):
                    wait = min(30, 2 ** (attempt + 1))
                    logger.warning("Rate limited (%s) on %s, waiting %ss", response.status_code, url, wait)
                    await asyncio.sleep(wait)
                    continue
                if response.status_code == 403:
                    logger.warning("Access denied (403) on %s — bot protection active", url)
                    # Don't retry 403 — the IP is likely blocked
                    return response
                return response
            except httpx.HTTPError as exc:
                logger.warning("HTTP error %s (attempt %s): %s", url, attempt + 1, exc)
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise RuntimeError(f"Failed to GET {url}")
