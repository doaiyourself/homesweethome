"""Integration test for run_daily_crawl with a stubbed Naver client.

Verifies the end-to-end flow:
    fake client → normalize → score → upsert → mark_inactive → report
without touching the network.
"""
from __future__ import annotations

import pytest

from app.models import Article, default_weights
from app.services.crawl_pipeline import run_daily_crawl
from app.services.user_pref_repository import update_pref


class FakeClient:
    """Stand-in for NaverLandClient: returns canned payloads per region."""

    def __init__(self, region_payloads: dict[str, list[dict]]):
        # region_payloads: { cortar_no: [pages...] }
        self._region_payloads = region_payloads
        self.calls: list[tuple[str, int]] = []

    def fetch_token(self, force: bool = False) -> str:
        return "fake-token"

    def fetch_regions(self, cortar_no: str) -> dict:
        return {"regionList": []}  # no children — input passes through

    def fetch_articles(self, cortar_no: str, *, page: int = 1, **_) -> dict:
        self.calls.append((cortar_no, page))
        pages = self._region_payloads.get(cortar_no, [])
        if page > len(pages):
            return {"articleList": [], "isMoreData": False}
        return pages[page - 1]


def _raw_article(article_no: str, **extra) -> dict:
    base = {
        "articleNo": article_no,
        "articleName": "신도림SK뷰",
        "tradeTypeCode": "B1",
        "realEstateTypeCode": "APT",
        "dealOrWarrantPrc": "5억",
        "rentPrc": None,
        "area1": 84.0,
        "area2": 59.0,
        "floorInfo": "12/25",
        "direction": "남향",
        "tagList": ["역세권"],
        "articleConfirmYmd": "20260514",
    }
    base.update(extra)
    return base


@pytest.mark.asyncio
async def test_full_flow_inserts_and_scores(session):
    # Setup prefs so scorer has something to grade against
    await update_pref(
        session,
        {
            "region_codes": ["1153010100"],
            "deposit_min": 10000,
            "deposit_max": 80000,
            "area_min_pyeong": 15,
            "area_max_pyeong": 30,
            "weights": default_weights(),
        },
    )
    await session.commit()

    fake = FakeClient(
        {
            "1153010100": [
                {
                    "articleList": [_raw_article("A001"), _raw_article("A002")],
                    "isMoreData": False,
                }
            ]
        }
    )
    report = await run_daily_crawl(session, client=fake)

    assert report.new_count == 2
    assert report.updated_count == 0
    assert report.error_count == 0
    assert report.average_score is not None and report.average_score > 0

    a1 = await session.get(Article, "A001")
    assert a1.is_active is True
    assert a1.score is not None and a1.score > 0


@pytest.mark.asyncio
async def test_second_run_marks_disappeared_inactive(session):
    await update_pref(
        session,
        {"region_codes": ["1153010100"], "weights": default_weights()},
    )
    await session.commit()

    fake1 = FakeClient(
        {"1153010100": [{"articleList": [_raw_article("A001"), _raw_article("A002")], "isMoreData": False}]}
    )
    await run_daily_crawl(session, client=fake1)

    # Second crawl: only A001 still present
    fake2 = FakeClient(
        {"1153010100": [{"articleList": [_raw_article("A001")], "isMoreData": False}]}
    )
    report = await run_daily_crawl(session, client=fake2)

    assert report.deactivated_count == 1
    a2 = await session.get(Article, "A002")
    assert a2.is_active is False
    a1 = await session.get(Article, "A001")
    assert a1.is_active is True


@pytest.mark.asyncio
async def test_gu_code_is_expanded(session):
    """A code ending in many zeros should trigger fetch_regions."""
    await update_pref(
        session,
        {"region_codes": ["1153000000"], "weights": default_weights()},
    )
    await session.commit()

    class ExpandingClient(FakeClient):
        def fetch_regions(self, cortar_no: str) -> dict:
            return {"regionList": [{"cortarNo": "1153010100"}, {"cortarNo": "1153010200"}]}

    fake = ExpandingClient(
        {
            "1153010100": [{"articleList": [_raw_article("A001")], "isMoreData": False}],
            "1153010200": [{"articleList": [_raw_article("A002")], "isMoreData": False}],
        }
    )
    report = await run_daily_crawl(session, client=fake)
    assert report.new_count == 2
    # Both child regions should have been called
    called_regions = {c[0] for c in fake.calls}
    assert called_regions == {"1153010100", "1153010200"}
