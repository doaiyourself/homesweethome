"""/api/prefs — GET and PUT the singleton UserPref row."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas import UserPrefRead, UserPrefUpdate
from app.services import user_pref_repository

router = APIRouter(prefix="/api/prefs", tags=["prefs"])


@router.get("", response_model=UserPrefRead)
async def get_prefs(session: AsyncSession = Depends(get_session)) -> UserPrefRead:
    pref = await user_pref_repository.get_or_create_pref(session)
    return UserPrefRead.model_validate(pref)


@router.put("", response_model=UserPrefRead)
async def update_prefs(
    body: UserPrefUpdate,
    session: AsyncSession = Depends(get_session),
) -> UserPrefRead:
    pref = await user_pref_repository.update_pref(
        session, body.model_dump(exclude_unset=True)
    )
    await session.commit()
    return UserPrefRead.model_validate(pref)
