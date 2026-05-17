"""Score an article against UserPref.

Each component returns a number in [0, 1]; the final score is the weighted
sum multiplied by 100. Components with no data (missing field, no
preference set) return None and are dropped from the average so they
don't drag the result down to zero.

Components:
    price_fit       — within [deposit_min, deposit_max]? closer to max = better
    area_fit        — within [area_min_pyeong, area_max_pyeong]? peak at midpoint
    floor_fit       — middle floors preferred; ground / top penalised
    direction_score — 남향 > 남동/남서 > 동/서 > 북
    keyword_score   — must_have boost, exclude penalty over text fields
    freshness       — recency of articleConfirmYmd (linear decay)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.models import UserPref


# --- Direction lookup -------------------------------------------------------
_DIRECTION_SCORES: dict[str, float] = {
    "남향": 1.00,
    "남동향": 0.85,
    "남서향": 0.85,
    "동향": 0.60,
    "서향": 0.55,
    "북동향": 0.35,
    "북서향": 0.35,
    "동남향": 0.85,  # alternative wording
    "서남향": 0.85,
    "북향": 0.20,
}


@dataclass
class ScoreBreakdown:
    """Per-component breakdown for debugging / explainability."""
    total: float  # 0..100
    components: dict[str, float | None]
    weights: dict[str, float]


# --- Individual components --------------------------------------------------

def _price_fit(article: dict[str, Any], pref: UserPref) -> float | None:
    """In-budget = good; the closer to deposit_max (within budget) the better."""
    deposit = article.get("deposit")
    if deposit is None:
        return None
    lo = pref.deposit_min
    hi = pref.deposit_max
    if lo is None and hi is None:
        return None
    if hi is not None and deposit > hi:
        return 0.0
    if lo is not None and deposit < lo:
        # Listings well below the floor are suspicious or off-spec; soft floor.
        return 0.3
    if lo is None:
        lo = 0
    if hi is None or hi == lo:
        return 0.8
    # Linear ramp 0.6 (at lo) → 1.0 (at hi).
    frac = (deposit - lo) / (hi - lo)
    return 0.6 + 0.4 * frac


def _area_fit(article: dict[str, Any], pref: UserPref) -> float | None:
    """Triangular preference centred on the midpoint of the pyeong range."""
    pyeong = article.get("area_pyeong")
    if pyeong is None:
        return None
    lo = pref.area_min_pyeong
    hi = pref.area_max_pyeong
    if lo is None and hi is None:
        return None
    if lo is not None and pyeong < lo:
        return 0.2
    if hi is not None and pyeong > hi:
        return 0.4  # too big is less bad than too small
    if lo is None:
        lo = 0.0
    if hi is None:
        return 1.0  # within open-ended upper bound
    mid = (lo + hi) / 2
    half = max((hi - lo) / 2, 0.001)
    distance_from_mid = abs(pyeong - mid)
    return max(0.0, 1.0 - distance_from_mid / half * 0.5)  # 1.0 at mid, 0.5 at edges


def _floor_fit(article: dict[str, Any], pref: UserPref) -> float | None:
    """Mid floors preferred, ground and top penalised."""
    current_raw = article.get("floor_current")
    total = article.get("floor_total")
    if current_raw is None or total is None or total <= 0:
        return None
    try:
        current = int(current_raw)
    except (TypeError, ValueError):
        # Non-numeric like 고/중/저 — return a neutral mid value.
        return 0.6
    if pref.floor_min is not None and current < pref.floor_min:
        return 0.1
    if current <= 1:
        return 0.3  # 1F
    if current >= total:
        return 0.5  # top floor — view but heat issues
    # Distance from middle: peak at total/2.
    mid = total / 2
    distance = abs(current - mid) / mid  # 0 at middle, ~1 at edges
    return max(0.4, 1.0 - distance * 0.6)


def _direction_score(article: dict[str, Any], pref: UserPref) -> float | None:
    """Lookup table; unknown direction returns 0.5 (neutral)."""
    direction = article.get("direction")
    if not direction:
        return None
    return _DIRECTION_SCORES.get(direction, 0.5)


def _keyword_score(article: dict[str, Any], pref: UserPref) -> float | None:
    """Scan description, tags, and complex_name for keywords from prefs."""
    must = pref.must_have_keywords or []
    exclude = pref.exclude_keywords or []
    if not must and not exclude:
        return None

    haystack_parts: list[str] = []
    for key in ("complex_name", "building_name", "description"):
        v = article.get(key)
        if v:
            haystack_parts.append(str(v))
    tags = article.get("tags") or []
    haystack_parts.extend(str(t) for t in tags)
    haystack = " ".join(haystack_parts)

    if not haystack:
        return None

    # Each must-match contributes 0.25 (cap when must list short); each
    # exclude-match subtracts 0.4. Final clipped to [0, 1].
    score = 0.5
    if must:
        hits = sum(1 for kw in must if kw in haystack)
        score += min(hits / max(len(must), 1), 1.0) * 0.5
    for kw in exclude:
        if kw in haystack:
            score -= 0.4
    return max(0.0, min(1.0, score))


def _freshness(article: dict[str, Any], pref: UserPref) -> float | None:
    """articleConfirmYmd is a YYYYMMDD string; newer is better. Linear decay."""
    ymd = article.get("article_confirm_ymd")
    if not ymd or len(ymd) != 8:
        return None
    try:
        confirm = date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
    except ValueError:
        return None
    days = (date.today() - confirm).days
    if days <= 0:
        return 1.0
    if days >= 60:
        return 0.1
    return max(0.1, 1.0 - days / 60 * 0.9)


# --- Public API -------------------------------------------------------------

_COMPONENT_FNS: dict[str, callable] = {
    "price_fit": _price_fit,
    "area_fit": _area_fit,
    "floor_fit": _floor_fit,
    "direction_score": _direction_score,
    "keyword_score": _keyword_score,
    "freshness": _freshness,
}


def score_article(article: dict[str, Any], pref: UserPref) -> ScoreBreakdown:
    """Compute a 0..100 score for one normalized article against the prefs.

    `article` is a dict (the output of crawler.parser.normalize_article).
    """
    weights = dict(pref.weights or {})
    component_values: dict[str, float | None] = {}
    weighted_sum = 0.0
    used_weight = 0.0

    for name, fn in _COMPONENT_FNS.items():
        value = fn(article, pref)
        component_values[name] = value
        weight = weights.get(name, 0.0)
        if value is not None and weight > 0:
            weighted_sum += value * weight
            used_weight += weight

    total = (weighted_sum / used_weight * 100.0) if used_weight > 0 else 0.0
    return ScoreBreakdown(
        total=round(total, 2),
        components=component_values,
        weights=weights,
    )
