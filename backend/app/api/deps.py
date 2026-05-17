"""Shared FastAPI dependencies (DB session + admin auth)."""
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a transactional DB session per request."""
    async with SessionLocal() as session:
        yield session


def require_admin_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = None,  # filled by the caller via Depends
) -> None:
    """Header-based admin guard. Compares against settings.admin_token."""
    settings = settings or get_settings()
    expected = settings.admin_token
    if not expected or expected == "change-me":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ADMIN_TOKEN is not configured on the server.",
        )
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin token.")
