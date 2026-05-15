"""Integration tests for article_repository — runs against in-memory SQLite."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import Article
from app.services.article_repository import (
    count_active,
    get_active_articles,
    get_new_articles_since,
    mark_inactive_except,
    upsert_article,
)


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _article_data(article_no: str, **overrides) -> dict:
    base = {
        "article_no": article_no,
        "complex_name": "신도림SK뷰",
        "trade_type": "B1",
        "real_estate_type": "APT",
        "deposit": 50000,
        "monthly_rent": None,
        "area_pyeong": 25.0,
        "cortar_no": "1153010100",
        "tags": ["역세권"],
        "raw_data": {"articleNo": article_no},
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
class TestUpsert:
    async def test_insert_new(self, session):
        result = await upsert_article(session, _article_data("A001"))
        assert result.was_new is True
        assert result.article.article_no == "A001"
        assert result.article.is_active is True
        assert result.article.deposit == 50000

    async def test_update_existing(self, session):
        await upsert_article(session, _article_data("A001", deposit=50000))
        # Same article reappears with new price
        result = await upsert_article(session, _article_data("A001", deposit=52000))
        assert result.was_new is False
        assert result.article.deposit == 52000

    async def test_update_preserves_first_seen_at(self, session):
        first = await upsert_article(session, _article_data("A001"))
        first_seen = first.article.first_seen_at
        # Make sure a subsequent upsert doesn't shift first_seen_at
        result = await upsert_article(session, _article_data("A001", deposit=55000))
        assert result.article.first_seen_at == first_seen

    async def test_missing_article_no_raises(self, session):
        with pytest.raises(ValueError):
            await upsert_article(session, {"article_no": None})


@pytest.mark.asyncio
class TestMarkInactive:
    async def test_flips_unseen(self, session):
        await upsert_article(session, _article_data("A001"))
        await upsert_article(session, _article_data("A002"))
        await upsert_article(session, _article_data("A003"))
        await session.commit()

        # Crawl only saw A001 + A002
        flipped = await mark_inactive_except(session, seen_article_nos=["A001", "A002"])
        assert flipped == 1
        a3 = await session.get(Article, "A003")
        assert a3.is_active is False

    async def test_cortar_scope(self, session):
        await upsert_article(session, _article_data("A001", cortar_no="X"))
        await upsert_article(session, _article_data("A002", cortar_no="Y"))
        await session.commit()

        # A region-Y-only crawl returned no listings; A001 in region X should
        # NOT be touched.
        flipped = await mark_inactive_except(session, seen_article_nos=[], cortar_no="Y")
        assert flipped == 1
        a1 = await session.get(Article, "A001")
        a2 = await session.get(Article, "A002")
        assert a1.is_active is True
        assert a2.is_active is False


@pytest.mark.asyncio
class TestQueries:
    async def test_get_active_filters_score(self, session):
        await upsert_article(session, _article_data("A001"))
        await upsert_article(session, _article_data("A002"))
        a1 = await session.get(Article, "A001")
        a2 = await session.get(Article, "A002")
        a1.score = 85.0
        a2.score = 60.0
        await session.commit()

        results = await get_active_articles(session, min_score=80.0)
        assert [a.article_no for a in results] == ["A001"]

    async def test_get_active_orders_by_score_desc(self, session):
        await upsert_article(session, _article_data("A001"))
        await upsert_article(session, _article_data("A002"))
        a1 = await session.get(Article, "A001")
        a2 = await session.get(Article, "A002")
        a1.score = 70.0
        a2.score = 90.0
        await session.commit()

        results = await get_active_articles(session)
        assert [a.article_no for a in results] == ["A002", "A001"]

    async def test_count_active(self, session):
        await upsert_article(session, _article_data("A001"))
        await upsert_article(session, _article_data("A002"))
        await session.commit()
        await mark_inactive_except(session, seen_article_nos=["A001"])
        assert await count_active(session) == 1

    async def test_get_new_since(self, session):
        await upsert_article(session, _article_data("A001"))
        await session.commit()
        past = _utcnow_naive() - timedelta(hours=1)
        future = _utcnow_naive() + timedelta(hours=1)
        assert len(await get_new_articles_since(session, past)) == 1
        assert len(await get_new_articles_since(session, future)) == 0
