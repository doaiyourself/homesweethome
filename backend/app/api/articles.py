"""/api/articles router — list, detail, favorite / hidden actions."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models import ActionType
from app.schemas import ArticleListResponse, ArticleRead
from app.services import article_repository as articles
from app.services import user_action_repository as actions

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _annotate(rows, action_map: dict[str, set[str]]) -> list[ArticleRead]:
    """Attach is_favorited / is_hidden flags from a UserAction lookup."""
    out: list[ArticleRead] = []
    for row in rows:
        types = action_map.get(row.article_no, set())
        item = ArticleRead.model_validate(row)
        item.is_favorited = ActionType.FAVORITE.value in types
        item.is_hidden = ActionType.HIDDEN.value in types
        out.append(item)
    return out


# IMPORTANT: /favorites must be declared before /{article_no} so FastAPI
# routes it as a literal segment instead of matching as a path param.
@router.get("/favorites", response_model=ArticleListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> ArticleListResponse:
    fav_ids = await actions.list_article_nos(session, ActionType.FAVORITE)
    if not fav_ids:
        return ArticleListResponse(items=[], total=0, page=page, page_size=page_size)

    rows, total = await articles.query_articles(
        session,
        status="all",
        include_article_nos=fav_ids,
        limit=page_size,
        offset=(page - 1) * page_size,
        sort="score",
    )
    action_map = await actions.actions_for_article_nos(
        session, [r.article_no for r in rows]
    )
    return ArticleListResponse(
        items=_annotate(rows, action_map),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    status_: Literal["active", "new", "all"] = Query("active", alias="status"),
    min_score: float | None = Query(None, ge=0, le=100),
    cortar_no: str | None = Query(None),
    trade_type: list[str] | None = Query(None),
    real_estate_type: list[str] | None = Query(None),
    sort: Literal["score", "date", "last_seen"] = Query("score"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    show_hidden: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> ArticleListResponse:
    hidden = set() if show_hidden else set(
        await actions.list_article_nos(session, ActionType.HIDDEN)
    )
    rows, total = await articles.query_articles(
        session,
        status=status_,
        cortar_no=cortar_no,
        trade_types=trade_type,
        real_estate_types=real_estate_type,
        min_score=min_score,
        exclude_article_nos=list(hidden) or None,
        limit=page_size,
        offset=(page - 1) * page_size,
        sort=sort,
    )
    action_map = await actions.actions_for_article_nos(
        session, [r.article_no for r in rows]
    )
    return ArticleListResponse(
        items=_annotate(rows, action_map),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_no}", response_model=ArticleRead)
async def get_article_detail(
    article_no: str, session: AsyncSession = Depends(get_session)
) -> ArticleRead:
    article = await articles.get_article(session, article_no)
    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")
    action_map = await actions.actions_for_article_nos(session, [article_no])
    return _annotate([article], action_map)[0]


@router.post("/{article_no}/favorite", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def add_favorite(
    article_no: str, session: AsyncSession = Depends(get_session)
) -> None:
    try:
        await actions.add_action(session, article_no, ActionType.FAVORITE)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    await session.commit()


@router.delete("/{article_no}/favorite", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_favorite(
    article_no: str, session: AsyncSession = Depends(get_session)
) -> None:
    removed = await actions.remove_action(session, article_no, ActionType.FAVORITE)
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "favorite not set")
    await session.commit()


@router.post("/{article_no}/hide", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def add_hide(
    article_no: str, session: AsyncSession = Depends(get_session)
) -> None:
    try:
        await actions.add_action(session, article_no, ActionType.HIDDEN)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    await session.commit()


@router.delete("/{article_no}/hide", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_hide(
    article_no: str, session: AsyncSession = Depends(get_session)
) -> None:
    removed = await actions.remove_action(session, article_no, ActionType.HIDDEN)
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "hide not set")
    await session.commit()
