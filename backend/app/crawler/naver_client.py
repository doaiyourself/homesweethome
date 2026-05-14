"""Naver Real Estate (new.land.naver.com) HTTP client.

The site's JSON API requires a bearer JWT that is embedded in the main page's
JS bundle. The token rotates periodically — we extract it on first use and
re-extract on 401.

The Naver response schema is not officially documented. We capture the raw
response so the caller can inspect unfamiliar fields. Field names referenced
in `parser.py` are best-effort and may need to be adjusted after the probe
script reveals the actual response shape.
"""
from __future__ import annotations

import logging
import random
import re
import time
from typing import Any

import requests

from .constants import (
    DEFAULT_HEADERS,
    DEFAULT_REAL_ESTATE_TYPES,
    DEFAULT_TRADE_TYPES,
    NAVER_LAND_API,
    NAVER_LAND_BASE,
)

logger = logging.getLogger(__name__)


class NaverLandError(Exception):
    """Base error for the Naver client. Carries request context for debugging."""

    def __init__(self, message: str, *, url: str | None = None, status: int | None = None):
        super().__init__(message)
        self.url = url
        self.status = status

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts = [super().__str__()]
        if self.status is not None:
            parts.append(f"status={self.status}")
        if self.url is not None:
            parts.append(f"url={self.url}")
        return " | ".join(parts)


class NaverLandBlockedError(NaverLandError):
    """Raised when the server signals blocking (403 / 429)."""


class NaverLandTokenError(NaverLandError):
    """Raised when token extraction fails."""


# Candidate regexes for JWT extraction from the landing page. neo.land.naver.com
# currently puts the bearer in <input id="token" data-token="..."> — that's the
# first pattern. Fallbacks cover prior wrappings and a last-resort JWT shape.
_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'data-token="(eyJ[A-Za-z0-9_.\-]+)"'),
    re.compile(r'"accessToken"\s*:\s*"(eyJ[A-Za-z0-9_.\-]+)"'),
    re.compile(r'Bearer\s+(eyJ[A-Za-z0-9_.\-]+)'),
    re.compile(r'window\.__token\s*=\s*"(eyJ[A-Za-z0-9_.\-]+)"'),
    re.compile(r'"(eyJ[A-Za-z0-9_.\-]{40,})"'),  # last-resort: any JWT-looking string
)


class NaverLandClient:
    """Thin wrapper around requests.Session with token handling and pacing.

    Usage:
        client = NaverLandClient(user_agent=..., min_sleep=1.0, max_sleep=3.0)
        regions = client.fetch_regions("1153000000")
        articles = client.fetch_articles("1153010100", page=1)
    """

    def __init__(
        self,
        *,
        user_agent: str,
        min_sleep: float = 1.0,
        max_sleep: float = 3.0,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        self._session = session or requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._session.headers["User-Agent"] = user_agent
        self._min_sleep = min_sleep
        self._max_sleep = max_sleep
        self._timeout = timeout
        self._token: str | None = None

    # ---- public API --------------------------------------------------------

    def fetch_token(self, *, force: bool = False) -> str:
        """Extract a fresh bearer token from the main page bundle."""
        if self._token and not force:
            return self._token

        url = f"{NAVER_LAND_BASE}/"
        logger.info("Fetching Naver landing page for token: %s", url)
        try:
            resp = self._session.get(url, timeout=self._timeout)
        except requests.RequestException as e:
            raise NaverLandTokenError(f"Failed to load landing page: {e}", url=url) from e

        if resp.status_code in (403, 429):
            raise NaverLandBlockedError(
                "Blocked while loading landing page", url=url, status=resp.status_code
            )
        if resp.status_code >= 400:
            raise NaverLandTokenError(
                f"Landing page returned {resp.status_code}",
                url=url,
                status=resp.status_code,
            )

        html = resp.text
        for pattern in _TOKEN_PATTERNS:
            match = pattern.search(html)
            if match:
                token = match.group(1)
                logger.info(
                    "Extracted token using pattern %r (len=%d, head=%s)",
                    pattern.pattern[:40],
                    len(token),
                    token[:20],
                )
                self._token = token
                self._session.headers["Authorization"] = f"Bearer {token}"
                return token

        raise NaverLandTokenError(
            "No token pattern matched the landing page. "
            "The page bundle may have changed or rendering is JS-only — "
            "consider switching to Playwright.",
            url=url,
        )

    def fetch_regions(self, cortar_no: str) -> dict[str, Any]:
        """List sub-regions of a cortarNo.

        Top-level (city) cortarNo ends in 00000000; gu in 00000; dong in 00.
        """
        url = f"{NAVER_LAND_API}/regions/list"
        params = {"cortarNo": cortar_no}
        return self._get_json(url, params=params)

    def fetch_articles(
        self,
        cortar_no: str,
        *,
        trade_types: list[str] | None = None,
        real_estate_types: list[str] | None = None,
        page: int = 1,
        order: str = "rank",
    ) -> dict[str, Any]:
        """Fetch one page of articles for a dong-level cortarNo.

        trade_types: list like ["B1", "B2"] (전세, 월세). Joined with ":".
        real_estate_types: list like ["APT", "OPST", "VL"]. Joined with ":".
        """
        url = f"{NAVER_LAND_API}/articles"
        params = {
            "cortarNo": cortar_no,
            "order": order,
            "realEstateType": ":".join(real_estate_types or DEFAULT_REAL_ESTATE_TYPES),
            "tradeType": ":".join(trade_types or DEFAULT_TRADE_TYPES),
            "page": page,
        }
        return self._get_json(url, params=params)

    def fetch_article_detail(self, article_no: str) -> dict[str, Any]:
        """Fetch detail page for a single article."""
        url = f"{NAVER_LAND_API}/articles/{article_no}"
        return self._get_json(url)

    # ---- internals ---------------------------------------------------------

    def _get_json(self, url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET with token retry, pacing, and structured errors."""
        if self._token is None:
            self.fetch_token()

        self._sleep()
        logger.debug("GET %s params=%s", url, params)
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
        except requests.RequestException as e:
            raise NaverLandError(f"Request failed: {e}", url=url) from e

        if resp.status_code == 401:
            logger.warning("401 — re-fetching token and retrying once")
            self.fetch_token(force=True)
            self._sleep()
            try:
                resp = self._session.get(url, params=params, timeout=self._timeout)
            except requests.RequestException as e:
                raise NaverLandError(f"Retry after 401 failed: {e}", url=url) from e

        if resp.status_code in (403, 429):
            raise NaverLandBlockedError(
                f"Blocked (status {resp.status_code}). "
                "Slow down or rotate IP / User-Agent.",
                url=url,
                status=resp.status_code,
            )
        if resp.status_code >= 400:
            raise NaverLandError(
                f"Unexpected status {resp.status_code}: {resp.text[:200]}",
                url=url,
                status=resp.status_code,
            )

        try:
            return resp.json()
        except ValueError as e:
            raise NaverLandError(
                f"Response was not JSON: {resp.text[:200]}", url=url
            ) from e

    def _sleep(self) -> None:
        delay = random.uniform(self._min_sleep, self._max_sleep)
        time.sleep(delay)
