"""HTTP client asynchrone partagé — httpx + tenacity + rate limiter par domaine.

Usage :
    from techpulse_scraper.http_client import HttpClient

    async with HttpClient() as client:
        response = await client.get("https://example.com")
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from types import TracebackType
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from techpulse_scraper.config import settings
from techpulse_scraper.logger import logger


class RateLimiter:
    """Rate limiter token bucket simple, par domaine.

    Exemple : 2s minimum entre 2 requêtes vers le même domaine.
    """

    def __init__(self, min_interval: float = 2.0) -> None:
        self.min_interval = min_interval
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, url: str) -> None:
        domain = urlparse(url).netloc
        async with self._locks[domain]:
            loop = asyncio.get_event_loop()
            now = loop.time()
            wait = (self._last_request[domain] + self.min_interval) - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request[domain] = loop.time()


class HttpClient:
    """Async HTTP client avec retry + rate limiting + logs structurés."""

    def __init__(
        self,
        rate_limit_interval: float | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.rate_limiter = RateLimiter(
            min_interval=rate_limit_interval or settings.rate_limit_per_domain
        )
        self.timeout = timeout or settings.http_timeout
        default_headers = {
            "User-Agent": settings.user_agent,
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        if headers:
            default_headers.update(headers)
        self._client: httpx.AsyncClient | None = None
        self._headers = default_headers

    async def __aenter__(self) -> HttpClient:
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
            http2=False,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        reraise=True,
    )
    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        await self.rate_limiter.acquire(url)
        assert self._client is not None, "Use `async with HttpClient() as client:`"
        logger.debug("HTTP {} {}", method, url)
        response = await self._client.request(method, url, **kwargs)
        if response.status_code in (429, 500, 502, 503, 504):
            logger.warning("HTTP {} sur {} → retry", response.status_code, url)
            response.raise_for_status()
        return response

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._request("POST", url, **kwargs)
