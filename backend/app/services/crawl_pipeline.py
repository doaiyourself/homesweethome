"""Daily crawl orchestration.

`run_daily_crawl(session)`:
    1. load UserPref (creates default if absent)
    2. for each region in prefs.region_codes
        - paginate through Naver API until isMoreData=False
        - normalize each article
        - score it
        - upsert into DB
    3. mark unseen-but-previously-active rows inactive (per region)
    4. return a `CrawlReport` summarising new / updated / deactivated counts
       and the list of newly-seen articles (used by the Telegram notifier).
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crawler.naver_client import NaverLandClient, NaverLandError
from app.crawler.parser import normalize_article_list
from app.models import Article
from app.services.article_repository import (
    UpsertResult,
    mark_inactive_except,
    upsert_article,
)
from app.services.scorer import score_article
from app.services.user_pref_repository import get_or_create_pref

logger = logging.getLogger(__name__)

MAX_PAGES_PER_REGION = 50  # safety cap


@dataclass
class CrawlReport:
    new_count: int = 0
    updated_count: int = 0
    deactivated_count: int = 0
    error_count: int = 0
    average_score: float | None = None
    new_articles: list[Article] = field(default_factory=list)
    per_region: dict[str, dict[str, int]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "new_count": self.new_count,
            "updated_count": self.updated_count,
            "deactivated_count": self.deactivated_count,
            "error_count": self.error_count,
            "average_score": self.average_score,
            "per_region": self.per_region,
        }


async def run_daily_crawl(
    session: AsyncSession,
    *,
    client: NaverLandClient | None = None,
) -> CrawlReport:
    settings = get_settings()
    pref = await get_or_create_pref(session)

    if not pref.region_codes:
        logger.warning("UserPref has no region_codes; nothing to crawl")
        return CrawlReport()

    if client is None:
        client = NaverLandClient(
            user_agent=settings.crawl_user_agent,
            min_sleep=settings.crawl_min_sleep_sec,
            max_sleep=settings.crawl_max_sleep_sec,
        )

    report = CrawlReport()
    score_accumulator: list[float] = []
    seen_by_region: dict[str, set[str]] = defaultdict(set)

    # Expand any gu / city-level codes (trailing zeros) into dong-level codes.
    # The /api/articles endpoint only returns results for the smallest unit.
    dong_codes = _expand_to_dong_codes(client, pref.region_codes)
    logger.info(
        "Crawling %d dong-level region(s) (expanded from %d input code(s))",
        len(dong_codes), len(pref.region_codes),
    )

    for cortar_no in dong_codes:
        region_stats = {"new": 0, "updated": 0, "errors": 0}
        try:
            articles = await _crawl_region(client, cortar_no)
        except NaverLandError as e:
            logger.exception("Region %s failed: %s", cortar_no, e)
            region_stats["errors"] += 1
            report.error_count += 1
            report.per_region[cortar_no] = region_stats
            continue

        for normalized in articles:
            article_no = normalized.get("article_no")
            if not article_no:
                continue
            seen_by_region[cortar_no].add(article_no)

            breakdown = score_article(normalized, pref)
            normalized_for_db = _to_db_payload(normalized, score=breakdown.total)

            try:
                result: UpsertResult = await upsert_article(session, normalized_for_db)
            except Exception:
                logger.exception("Upsert failed for %s", article_no)
                region_stats["errors"] += 1
                report.error_count += 1
                continue

            if result.was_new:
                region_stats["new"] += 1
                report.new_count += 1
                report.new_articles.append(result.article)
            else:
                region_stats["updated"] += 1
                report.updated_count += 1
            score_accumulator.append(breakdown.total)

        await session.commit()

        deactivated = await mark_inactive_except(
            session,
            seen_article_nos=seen_by_region[cortar_no],
            cortar_no=cortar_no,
        )
        await session.commit()
        region_stats["deactivated"] = deactivated
        report.deactivated_count += deactivated
        report.per_region[cortar_no] = region_stats

    if score_accumulator:
        report.average_score = round(sum(score_accumulator) / len(score_accumulator), 2)
    return report


def _expand_to_dong_codes(
    client: NaverLandClient, codes: list[str]
) -> list[str]:
    """Resolve any gu/si codes into the dong codes underneath them.

    A cortarNo ending in 5+ zeros is treated as gu-level (e.g. 1153000000 =
    Guro-gu). For each such code we call fetch_regions and collect the
    children's cortarNos. Codes that already look dong-level pass through.
    """
    result: list[str] = []
    seen: set[str] = set()

    def _add(code: str) -> None:
        if code and code not in seen:
            seen.add(code)
            result.append(code)

    for code in codes:
        if not code:
            continue
        if not code.endswith("00000"):
            _add(code)
            continue
        try:
            payload = client.fetch_regions(code)
        except NaverLandError:
            logger.exception("Failed to expand region %s; using as-is", code)
            _add(code)
            continue
        children = _extract_region_codes(payload)
        if not children:
            logger.warning("Region %s expanded to 0 children — using as-is", code)
            _add(code)
            continue
        for child in children:
            _add(child)
    return result


def _extract_region_codes(payload: dict) -> list[str]:
    """Pull cortarNo strings out of a /api/regions/list response."""
    out: list[str] = []
    for key in ("regionList", "list", "regions"):
        items = payload.get(key)
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                code = item.get("cortarNo") or item.get("CortarNo") or item.get("cortarno")
                if code:
                    out.append(str(code))
            if out:
                return out
    return out


async def _crawl_region(
    client: NaverLandClient, cortar_no: str
) -> list[dict]:
    """Fetch every page for `cortar_no` (until isMoreData=False)."""
    all_articles: list[dict] = []
    for page in range(1, MAX_PAGES_PER_REGION + 1):
        payload = client.fetch_articles(cortar_no, page=page)
        normalized = normalize_article_list(payload, cortar_no=cortar_no)
        all_articles.extend(normalized)
        if not payload.get("isMoreData", False):
            logger.info(
                "Region %s page=%d: collected %d (no more pages)",
                cortar_no, page, len(all_articles),
            )
            break
    else:
        logger.warning(
            "Region %s hit MAX_PAGES_PER_REGION=%d; assuming Naver throttled or "
            "the cap is too low.", cortar_no, MAX_PAGES_PER_REGION,
        )
    return all_articles


def _to_db_payload(normalized: dict, *, score: float) -> dict:
    """Convert normalize_article output into kwargs for the Article model.

    Drops the `raw` key (lives under raw_data instead), adds score, and
    ensures `tags` is a list.
    """
    payload = dict(normalized)
    raw = payload.pop("raw", None)
    payload["raw_data"] = raw
    payload["score"] = score
    payload["tags"] = payload.get("tags") or []
    return payload
