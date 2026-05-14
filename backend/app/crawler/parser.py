"""Parse and normalize Naver Real Estate responses.

The exact field names of the Naver response are not officially documented and
have varied. We default to the most commonly observed keys but keep the full
original payload under `raw` so callers can recover from misses.

Run `scripts/probe_crawler.py` first to inspect the actual shape, then tighten
the field mapping here.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# 1 평 = 3.305785 ㎡
SQM_PER_PYEONG = 3.305785

_PRICE_RE_EOK = re.compile(r"(\d+)\s*억")
_PRICE_RE_MAN = re.compile(r"([\d,]+)\s*(?:만)?\s*$")
_FLOOR_RE = re.compile(r"^\s*([A-Za-z가-힣\d]+)\s*/\s*(\d+)\s*$")


def parse_price(text: str | None) -> int | None:
    """Convert a Korean price string to 만원 (10,000 KRW) units.

    Examples:
        "8억 5,000" -> 85000
        "8억"       -> 80000
        "5,000"     -> 5000
        "1억 500"   -> 10500
        None / ""   -> None
    """
    if not text:
        return None
    text = text.replace(" ", "").replace("\xa0", "")

    eok_total = 0
    eok_match = _PRICE_RE_EOK.search(text)
    if eok_match:
        eok_total = int(eok_match.group(1)) * 10000  # 1억 = 10,000 만원
        text = text[eok_match.end():]

    man_total = 0
    if text:
        man_match = _PRICE_RE_MAN.search(text)
        if man_match:
            num = man_match.group(1).replace(",", "")
            if num.isdigit():
                man_total = int(num)

    total = eok_total + man_total
    return total if total > 0 else None


def parse_floor_info(text: str | None) -> tuple[str | None, int | None]:
    """Parse a floor string like "12/25" into (current, total).

    Current floor may be non-numeric (e.g. "고/25", "B1/25", "탑/25") so we
    return it as a string. Total is always int when parseable.
    """
    if not text:
        return None, None
    match = _FLOOR_RE.match(text)
    if not match:
        return text.strip() or None, None
    current_str = match.group(1)
    total = int(match.group(2))
    return current_str, total


def sqm_to_pyeong(sqm: float | None) -> float | None:
    if sqm is None or sqm <= 0:
        return None
    return round(sqm / SQM_PER_PYEONG, 2)


def _f(data: dict[str, Any], *keys: str) -> Any:
    """Return the first non-None value among the given keys."""
    for k in keys:
        v = data.get(k)
        if v is not None and v != "":
            return v
    return None


def normalize_article(raw: dict[str, Any], *, cortar_no: str | None = None) -> dict[str, Any]:
    """Convert one Naver article dict into our flat schema.

    The output keeps the original payload under `raw` so the DB layer can
    persist it for forensic debugging.

    Field names tried are best-effort based on observed Naver responses
    (may include: articleNo, atclNo, articleName, tradeTypeCode, dealOrWarrantPrc,
    rentPrc, area1, area2, floorInfo, direction, tagList, latitude, longitude,
    realtorName, articleConfirmYmd, ...).
    """
    article_no = _f(raw, "articleNo", "atclNo", "article_no")
    article_no = str(article_no) if article_no is not None else None

    area1_sqm = _f(raw, "area1", "spc1", "supplyArea")  # 공급면적
    area2_sqm = _f(raw, "area2", "spc2", "exclusiveArea")  # 전용면적
    try:
        area1_sqm = float(area1_sqm) if area1_sqm is not None else None
    except (TypeError, ValueError):
        area1_sqm = None
    try:
        area2_sqm = float(area2_sqm) if area2_sqm is not None else None
    except (TypeError, ValueError):
        area2_sqm = None

    floor_text = _f(raw, "floorInfo", "flrInfo")
    floor_current, floor_total = parse_floor_info(floor_text)

    # Prices: Naver sometimes returns numeric (만원) directly, sometimes strings.
    deposit_raw = _f(raw, "dealOrWarrantPrc", "prc", "warrantPrc")
    monthly_raw = _f(raw, "rentPrc", "rentPrice")
    deposit = _coerce_price(deposit_raw)
    monthly = _coerce_price(monthly_raw)

    lat = _f(raw, "latitude", "lat")
    lng = _f(raw, "longitude", "lng", "lon")
    try:
        lat = float(lat) if lat is not None else None
    except (TypeError, ValueError):
        lat = None
    try:
        lng = float(lng) if lng is not None else None
    except (TypeError, ValueError):
        lng = None

    return {
        "article_no": article_no,
        "complex_name": _f(raw, "articleName", "atclNm", "complexName"),
        "building_name": _f(raw, "buildingName", "bildNm"),
        "trade_type": _f(raw, "tradeTypeCode", "tradeTpCd"),
        "trade_type_name": _f(raw, "tradeTypeName", "tradeTpNm"),
        "real_estate_type": _f(raw, "realEstateTypeCode", "rletTpCd"),
        "real_estate_type_name": _f(raw, "realEstateTypeName", "rletTpNm"),
        "deposit": deposit,
        "monthly_rent": monthly,
        "price_display": _f(raw, "dealOrWarrantPrc", "prc"),
        "area1_sqm": area1_sqm,
        "area2_sqm": area2_sqm,
        "area_pyeong": sqm_to_pyeong(area2_sqm or area1_sqm),
        "floor_current": floor_current,
        "floor_total": floor_total,
        "direction": _f(raw, "direction", "drctn"),
        "description": _f(raw, "articleFeatureDesc", "atclFetrDesc", "description"),
        "tags": _f(raw, "tagList", "tags") or [],
        "latitude": lat,
        "longitude": lng,
        "cortar_no": cortar_no,
        "image_url": _f(raw, "representativeImgUrl", "repImgUrl"),
        "cp_name": _f(raw, "realtorName", "rltrNm", "cpName"),
        "cp_article_url": _f(raw, "cpPcArticleUrl"),
        "article_status": _f(raw, "articleStatus"),
        "verification_type": _f(raw, "verificationTypeCode"),
        "article_confirm_ymd": _f(raw, "articleConfirmYmd", "atclCfmYmd"),
        "raw": raw,
    }


def _coerce_price(value: Any) -> int | None:
    """Coerce a price field to int 만원, handling both numeric and string inputs."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None
    if isinstance(value, str):
        return parse_price(value)
    return None


def normalize_article_list(payload: dict[str, Any], *, cortar_no: str | None = None) -> list[dict[str, Any]]:
    """Extract the list of articles from a fetch_articles response and normalize each."""
    candidates = ("articleList", "atclList", "articles", "list")
    articles_raw = None
    for key in candidates:
        if isinstance(payload.get(key), list):
            articles_raw = payload[key]
            break
    if articles_raw is None:
        logger.warning(
            "No article list key found in response (tried %s). Top-level keys: %s",
            candidates,
            list(payload.keys()),
        )
        return []
    return [normalize_article(a, cortar_no=cortar_no) for a in articles_raw]
