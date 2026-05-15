"""Pydantic schema for UserPref."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserPrefBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str = "default"
    region_codes: list[str] = Field(default_factory=list)
    trade_types: list[str] = Field(default_factory=list)
    real_estate_types: list[str] = Field(default_factory=list)
    deposit_min: int | None = None
    deposit_max: int | None = None
    monthly_rent_max: int | None = None
    area_min_pyeong: float | None = None
    area_max_pyeong: float | None = None
    floor_min: int | None = None
    must_have_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)


class UserPrefRead(UserPrefBase):
    id: int


class UserPrefUpdate(UserPrefBase):
    """Body for PUT /api/prefs — every field is optional in the route layer."""
