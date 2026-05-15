"""Article model — one row per Naver listing."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Article(Base):
    __tablename__ = "articles"

    article_no: Mapped[str] = mapped_column(String(32), primary_key=True)

    # Identity / description
    complex_name: Mapped[str | None] = mapped_column(String(255))
    building_name: Mapped[str | None] = mapped_column(String(255))

    # Type codes
    trade_type: Mapped[str | None] = mapped_column(String(8), index=True)  # B1/B2
    trade_type_name: Mapped[str | None] = mapped_column(String(32))
    real_estate_type: Mapped[str | None] = mapped_column(String(16), index=True)
    real_estate_type_name: Mapped[str | None] = mapped_column(String(32))

    # Pricing in 만원 units
    deposit: Mapped[int | None] = mapped_column(Integer, index=True)
    monthly_rent: Mapped[int | None] = mapped_column(Integer)
    price_display: Mapped[str | None] = mapped_column(String(64))

    # Area
    area1_sqm: Mapped[float | None] = mapped_column(Float)  # 공급면적
    area2_sqm: Mapped[float | None] = mapped_column(Float)  # 전용면적
    area_pyeong: Mapped[float | None] = mapped_column(Float, index=True)

    # Floor
    floor_current: Mapped[str | None] = mapped_column(String(16))
    floor_total: Mapped[int | None] = mapped_column(Integer)

    # Orientation, description, tags
    direction: Mapped[str | None] = mapped_column(String(16))
    description: Mapped[str | None] = mapped_column(String(1024))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Location
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    cortar_no: Mapped[str | None] = mapped_column(String(16), index=True)
    address_text: Mapped[str | None] = mapped_column(String(255))

    # Images / broker
    image_url: Mapped[str | None] = mapped_column(String(512))
    cp_name: Mapped[str | None] = mapped_column(String(128))
    cp_article_url: Mapped[str | None] = mapped_column(String(512))

    # Status flags from source
    article_status: Mapped[str | None] = mapped_column(String(16))
    verification_type: Mapped[str | None] = mapped_column(String(32))
    article_confirm_ymd: Mapped[str | None] = mapped_column(String(8))

    # Forensic copy of the original payload
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Tracking
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Score (filled in by the scoring service)
    score: Mapped[float | None] = mapped_column(Float, index=True)


# Composite index that powers the common "active listings in a region" query.
Index(
    "ix_articles_active_region",
    Article.is_active,
    Article.cortar_no,
    Article.score,
)
