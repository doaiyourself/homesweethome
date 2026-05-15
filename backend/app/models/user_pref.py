"""UserPref — singleton row (id=1) holding our search criteria + scoring weights."""
from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

SINGLETON_ID = 1


class UserPref(Base, TimestampMixin):
    __tablename__ = "user_prefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SINGLETON_ID)

    label: Mapped[str] = mapped_column(String(64), default="default", nullable=False)

    # Region / type filters
    region_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    trade_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    real_estate_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Budget (만원)
    deposit_min: Mapped[int | None] = mapped_column(Integer)
    deposit_max: Mapped[int | None] = mapped_column(Integer)
    monthly_rent_max: Mapped[int | None] = mapped_column(Integer)

    # Area (평)
    area_min_pyeong: Mapped[float | None] = mapped_column(Float)
    area_max_pyeong: Mapped[float | None] = mapped_column(Float)

    # Floor
    floor_min: Mapped[int | None] = mapped_column(Integer)

    # Keyword scoring
    must_have_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exclude_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Scoring weights — keys: price_fit, area_fit, floor_fit, direction_score,
    # keyword_score, freshness. Values in [0, 1].
    weights: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


def default_weights() -> dict[str, float]:
    return {
        "price_fit": 0.30,
        "area_fit": 0.20,
        "floor_fit": 0.10,
        "direction_score": 0.10,
        "keyword_score": 0.20,
        "freshness": 0.10,
    }
