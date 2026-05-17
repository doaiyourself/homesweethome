"""Favorite / hidden actions per article."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionType, Article, UserAction


async def add_action(
    session: AsyncSession, article_no: str, action_type: ActionType
) -> UserAction:
    article = await session.get(Article, article_no)
    if article is None:
        raise LookupError(f"article {article_no} not found")

    existing = await _find_action(session, article_no, action_type)
    if existing is not None:
        return existing
    action = UserAction(article_no=article_no, action_type=action_type.value)
    session.add(action)
    await session.flush()
    return action


async def remove_action(
    session: AsyncSession, article_no: str, action_type: ActionType
) -> bool:
    """Return True if a row was deleted, False if it didn't exist."""
    stmt = delete(UserAction).where(
        UserAction.article_no == article_no,
        UserAction.action_type == action_type.value,
    )
    result = await session.execute(stmt)
    return (result.rowcount or 0) > 0


async def list_article_nos(
    session: AsyncSession, action_type: ActionType
) -> list[str]:
    stmt = select(UserAction.article_no).where(
        UserAction.action_type == action_type.value
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def actions_for_article_nos(
    session: AsyncSession, article_nos: list[str]
) -> dict[str, set[str]]:
    """Map article_no -> set of action_type strings applied to it."""
    if not article_nos:
        return {}
    stmt = select(UserAction.article_no, UserAction.action_type).where(
        UserAction.article_no.in_(article_nos)
    )
    out: dict[str, set[str]] = {}
    for art_no, action_type in await session.execute(stmt):
        out.setdefault(art_no, set()).add(action_type)
    return out


async def _find_action(
    session: AsyncSession, article_no: str, action_type: ActionType
) -> UserAction | None:
    stmt = select(UserAction).where(
        UserAction.article_no == article_no,
        UserAction.action_type == action_type.value,
    )
    return (await session.execute(stmt)).scalar_one_or_none()
