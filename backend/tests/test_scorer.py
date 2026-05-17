"""Unit tests for the scoring function — pure logic, no DB."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models import UserPref, default_weights
from app.services.scorer import score_article


def make_pref(**overrides) -> UserPref:
    pref = UserPref(
        id=1,
        label="test",
        region_codes=[],
        trade_types=["B1", "B2"],
        real_estate_types=["APT", "OPST"],
        must_have_keywords=[],
        exclude_keywords=[],
        weights=default_weights(),
    )
    for k, v in overrides.items():
        setattr(pref, k, v)
    return pref


def make_article(**overrides) -> dict:
    art = {
        "article_no": "X",
        "complex_name": "신도림SK뷰",
        "trade_type": "B1",
        "deposit": 50000,
        "monthly_rent": None,
        "area_pyeong": 25.0,
        "floor_current": "15",
        "floor_total": 25,
        "direction": "남향",
        "description": "역세권 신축",
        "tags": ["역세권"],
        "article_confirm_ymd": date.today().strftime("%Y%m%d"),
    }
    art.update(overrides)
    return art


class TestPriceFit:
    def test_overbudget_zero(self):
        pref = make_pref(deposit_min=10000, deposit_max=40000)
        result = score_article(make_article(deposit=50000), pref)
        assert result.components["price_fit"] == 0.0

    def test_in_budget_high(self):
        pref = make_pref(deposit_min=10000, deposit_max=60000)
        # At max → should be ~1.0
        result = score_article(make_article(deposit=60000), pref)
        assert pytest.approx(result.components["price_fit"], abs=0.01) == 1.0

    def test_in_budget_low(self):
        pref = make_pref(deposit_min=10000, deposit_max=60000)
        # At min → should be ~0.6
        result = score_article(make_article(deposit=10000), pref)
        assert pytest.approx(result.components["price_fit"], abs=0.01) == 0.6

    def test_no_pref_returns_none(self):
        pref = make_pref()
        result = score_article(make_article(), pref)
        assert result.components["price_fit"] is None


class TestAreaFit:
    def test_below_min(self):
        pref = make_pref(area_min_pyeong=20, area_max_pyeong=40)
        r = score_article(make_article(area_pyeong=15.0), pref)
        assert r.components["area_fit"] == 0.2

    def test_above_max(self):
        pref = make_pref(area_min_pyeong=20, area_max_pyeong=40)
        r = score_article(make_article(area_pyeong=50.0), pref)
        assert r.components["area_fit"] == 0.4

    def test_at_midpoint_is_one(self):
        pref = make_pref(area_min_pyeong=20, area_max_pyeong=40)
        r = score_article(make_article(area_pyeong=30.0), pref)
        assert pytest.approx(r.components["area_fit"], abs=0.01) == 1.0


class TestFloorFit:
    def test_first_floor_low(self):
        pref = make_pref()
        r = score_article(make_article(floor_current="1", floor_total=25), pref)
        assert r.components["floor_fit"] == 0.3

    def test_top_floor_medium(self):
        pref = make_pref()
        r = score_article(make_article(floor_current="25", floor_total=25), pref)
        assert r.components["floor_fit"] == 0.5

    def test_middle_floor_high(self):
        pref = make_pref()
        r = score_article(make_article(floor_current="12", floor_total=25), pref)
        # Mid-ish should be near 1.0
        assert r.components["floor_fit"] > 0.9

    def test_below_floor_min(self):
        pref = make_pref(floor_min=10)
        r = score_article(make_article(floor_current="5", floor_total=25), pref)
        assert r.components["floor_fit"] == 0.1

    def test_non_numeric(self):
        pref = make_pref()
        r = score_article(make_article(floor_current="고", floor_total=25), pref)
        assert r.components["floor_fit"] == 0.6


class TestDirection:
    def test_south_top(self):
        pref = make_pref()
        r = score_article(make_article(direction="남향"), pref)
        assert r.components["direction_score"] == 1.0

    def test_north_low(self):
        pref = make_pref()
        r = score_article(make_article(direction="북향"), pref)
        assert r.components["direction_score"] == 0.2

    def test_unknown_neutral(self):
        pref = make_pref()
        r = score_article(make_article(direction="신기한향"), pref)
        assert r.components["direction_score"] == 0.5

    def test_missing(self):
        pref = make_pref()
        r = score_article(make_article(direction=None), pref)
        assert r.components["direction_score"] is None


class TestKeywords:
    def test_must_have_boost(self):
        pref = make_pref(must_have_keywords=["역세권"])
        r = score_article(make_article(tags=["역세권"]), pref)
        assert r.components["keyword_score"] == 1.0

    def test_exclude_penalty(self):
        pref = make_pref(exclude_keywords=["반지하"])
        r = score_article(make_article(description="반지하 매물"), pref)
        assert r.components["keyword_score"] == pytest.approx(0.1, abs=0.01)

    def test_neither(self):
        pref = make_pref()
        r = score_article(make_article(), pref)
        assert r.components["keyword_score"] is None


class TestFreshness:
    def test_today_top(self):
        pref = make_pref()
        ymd = date.today().strftime("%Y%m%d")
        r = score_article(make_article(article_confirm_ymd=ymd), pref)
        assert r.components["freshness"] == 1.0

    def test_old_floor(self):
        pref = make_pref()
        old = (date.today() - timedelta(days=120)).strftime("%Y%m%d")
        r = score_article(make_article(article_confirm_ymd=old), pref)
        assert r.components["freshness"] == 0.1


class TestTotal:
    def test_total_is_weighted_sum_times_100(self):
        # All weights equal, all components = 1.0 ideally → 100
        pref = make_pref(
            deposit_min=10000,
            deposit_max=60000,
            area_min_pyeong=20,
            area_max_pyeong=40,
            must_have_keywords=["역세권"],
        )
        r = score_article(
            make_article(
                deposit=60000,
                area_pyeong=30,
                floor_current="12",
                floor_total=25,
                direction="남향",
                tags=["역세권"],
            ),
            pref,
        )
        assert r.total > 95.0  # all top-tier inputs

    def test_total_zero_with_no_used_weights(self):
        # No prefs set at all → all components return None → total=0
        pref = make_pref(weights={})
        r = score_article(make_article(direction=None, article_confirm_ymd=None), pref)
        assert r.total == 0.0
