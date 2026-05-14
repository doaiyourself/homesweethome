"""Sanity tests for parser utilities. No network involved."""
from __future__ import annotations

from app.crawler.parser import (
    normalize_article,
    parse_floor_info,
    parse_price,
    sqm_to_pyeong,
)


class TestParsePrice:
    def test_eok_and_man(self):
        assert parse_price("8억 5,000") == 85000

    def test_eok_only(self):
        assert parse_price("8억") == 80000

    def test_man_only(self):
        assert parse_price("5,000") == 5000

    def test_small_man_after_eok(self):
        assert parse_price("1억 500") == 10500

    def test_none(self):
        assert parse_price(None) is None
        assert parse_price("") is None


class TestParseFloorInfo:
    def test_numeric(self):
        assert parse_floor_info("12/25") == ("12", 25)

    def test_non_numeric_current(self):
        assert parse_floor_info("고/25") == ("고", 25)

    def test_empty(self):
        assert parse_floor_info(None) == (None, None)

    def test_malformed(self):
        assert parse_floor_info("garbage") == ("garbage", None)


class TestSqmToPyeong:
    def test_normal(self):
        assert sqm_to_pyeong(33.0577) == 10.0

    def test_zero(self):
        assert sqm_to_pyeong(0) is None

    def test_none(self):
        assert sqm_to_pyeong(None) is None


class TestNormalizeArticle:
    def test_keeps_raw(self):
        raw = {"articleNo": "12345", "dealOrWarrantPrc": "3억"}
        n = normalize_article(raw)
        assert n["raw"] is raw
        assert n["article_no"] == "12345"
        assert n["deposit"] == 30000

    def test_missing_fields_dont_crash(self):
        n = normalize_article({})
        assert n["article_no"] is None
        assert n["deposit"] is None
        assert n["tags"] == []
