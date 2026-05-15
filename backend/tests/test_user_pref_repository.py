"""Tests for the singleton UserPref repository."""
from __future__ import annotations

import pytest

from app.services.user_pref_repository import get_or_create_pref, update_pref


@pytest.mark.asyncio
async def test_get_or_create_initializes_with_defaults(session):
    pref = await get_or_create_pref(session)
    assert pref.id == 1
    assert pref.label == "default"
    assert isinstance(pref.weights, dict)
    assert "price_fit" in pref.weights


@pytest.mark.asyncio
async def test_get_or_create_is_idempotent(session):
    p1 = await get_or_create_pref(session)
    p2 = await get_or_create_pref(session)
    assert p1.id == p2.id == 1


@pytest.mark.asyncio
async def test_update_pref_persists(session):
    await get_or_create_pref(session)
    pref = await update_pref(
        session,
        {"deposit_max": 80000, "must_have_keywords": ["역세권", "신축"]},
    )
    assert pref.deposit_max == 80000
    assert pref.must_have_keywords == ["역세권", "신축"]
