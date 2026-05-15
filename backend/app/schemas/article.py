"""Pydantic schemas for the Article model (API + service layer DTOs)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
    """Fields shared by ingestion and read schemas."""

    model_config = ConfigDict(from_attributes=True)

    article_no: str
    complex_name: str | None = None
    building_name: str | None = None
    trade_type: str | None = None
    trade_type_name: str | None = None
    real_estate_type: str | None = None
    real_estate_type_name: str | None = None
    deposit: int | None = None
    monthly_rent: int | None = None
    price_display: str | None = None
    area1_sqm: float | None = None
    area2_sqm: float | None = None
    area_pyeong: float | None = None
    floor_current: str | None = None
    floor_total: int | None = None
    direction: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    cortar_no: str | None = None
    address_text: str | None = None
    image_url: str | None = None
    cp_name: str | None = None
    cp_article_url: str | None = None
    article_status: str | None = None
    verification_type: str | None = None
    article_confirm_ymd: str | None = None


class ArticleIngest(ArticleBase):
    """Input shape for the upsert path."""

    raw_data: dict[str, Any] | None = None


class ArticleRead(ArticleBase):
    """Output shape for the API. Excludes the raw payload by default."""

    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    score: float | None = None
