"""Repository for the singleton UserPref row."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SINGLETON_ID, UserPref, default_weights


async def get_or_create_pref(session: AsyncSession) -> UserPref:
    pref = await session.get(UserPref, SINGLETON_ID)
    if pref is None:
        pref = UserPref(
            id=SINGLETON_ID,
            label="default",
            region_codes=[],
            trade_types=[],
            real_estate_types=[],
            must_have_keywords=[],
            exclude_keywords=[],
            weights=default_weights(),
        )
        session.add(pref)
        await session.flush()
    return pref


async def update_pref(session: AsyncSession, data: dict[str, Any]) -> UserPref:
    pref = await get_or_create_pref(session)
    for key, value in data.items():
        if hasattr(pref, key) and key != "id":
            setattr(pref, key, value)
    await session.flush()
    return pref
