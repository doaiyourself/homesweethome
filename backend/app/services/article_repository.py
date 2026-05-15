"""Article persistence layer.

Each daily crawl call:
    1. iterates the normalized articles and calls `upsert_article` per row
    2. after the loop, calls `mark_inactive_except` with the set of seen
       article_nos so listings that vanished get flipped to is_active=False.

The query helpers cover the read paths the API will need.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _utcnow_naive() -> datetime:
    """UTC clock as a naive datetime — matches SQLite's `func.now()` storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article


@dataclass
class UpsertResult:
    article: Article
    was_new: bool


async def upsert_article(session: AsyncSession, data: dict[str, Any]) -> UpsertResult:
    """Insert a new article or refresh the existing row.

    On insert: writes every field.
    On update: refreshes mutable fields (price, status, raw_data) and
    bumps last_seen_at + is_active. first_seen_at is preserved.
    """
    article_no = data["article_no"]
    if not article_no:
        raise ValueError("article_no is required for upsert")

    existing = await session.get(Article, article_no)
    if existing is None:
        article = Article(**data)
        article.is_active = True
        session.add(article)
        await session.flush()
        return UpsertResult(article=article, was_new=True)

    # Refresh mutable columns. Identity fields (article_no, complex_name) are
    # left alone — if Naver flips them, we want to notice in raw_data not
    # silently overwrite.
    mutable = (
        "deposit",
        "monthly_rent",
        "price_display",
        "floor_current",
        "floor_total",
        "direction",
        "description",
        "tags",
        "image_url",
        "cp_article_url",
        "article_status",
        "verification_type",
        "article_confirm_ymd",
        "raw_data",
        "score",
    )
    for field in mutable:
        if field in data:
            setattr(existing, field, data[field])
    existing.is_active = True
    existing.last_seen_at = _utcnow_naive()
    await session.flush()
    return UpsertResult(article=existing, was_new=False)


async def mark_inactive_except(
    session: AsyncSession,
    *,
    seen_article_nos: Iterable[str],
    cortar_no: str | None = None,
) -> int:
    """Flip `is_active` to False for any active row not in `seen_article_nos`.

    Optional `cortar_no` filter scopes the operation so a partial crawl of one
    region doesn't deactivate listings from regions we didn't visit.
    Returns the number of rows flipped.
    """
    seen_set = set(seen_article_nos)
    stmt = update(Article).where(Article.is_active.is_(True))
    if cortar_no is not None:
        stmt = stmt.where(Article.cortar_no == cortar_no)
    if seen_set:
        stmt = stmt.where(Article.article_no.notin_(seen_set))
    stmt = stmt.values(is_active=False)
    result = await session.execute(stmt)
    return result.rowcount or 0


async def get_article(session: AsyncSession, article_no: str) -> Article | None:
    return await session.get(Article, article_no)


async def get_active_articles(
    session: AsyncSession,
    *,
    cortar_no: str | None = None,
    trade_types: Sequence[str] | None = None,
    min_score: float | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "score_desc",
) -> list[Article]:
    stmt = select(Article).where(Article.is_active.is_(True))
    if cortar_no is not None:
        stmt = stmt.where(Article.cortar_no == cortar_no)
    if trade_types:
        stmt = stmt.where(Article.trade_type.in_(trade_types))
    if min_score is not None:
        stmt = stmt.where(Article.score >= min_score)

    if order_by == "score_desc":
        stmt = stmt.order_by(Article.score.desc().nullslast(), Article.last_seen_at.desc())
    elif order_by == "newest":
        stmt = stmt.order_by(Article.first_seen_at.desc())
    else:
        stmt = stmt.order_by(Article.last_seen_at.desc())

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_new_articles_since(
    session: AsyncSession, since: datetime, *, min_score: float | None = None
) -> list[Article]:
    stmt = (
        select(Article)
        .where(Article.first_seen_at >= since)
        .where(Article.is_active.is_(True))
    )
    if min_score is not None:
        stmt = stmt.where(Article.score >= min_score)
    stmt = stmt.order_by(Article.score.desc().nullslast(), Article.first_seen_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_active(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count()).select_from(Article).where(Article.is_active.is_(True))
    )
    return int(result.scalar_one())
