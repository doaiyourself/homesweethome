"""/api/stats — counts and aggregates for the dashboard."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models import Article
from app.services.article_repository import _utcnow_naive, count_active

router = APIRouter(prefix="/api/stats", tags=["stats"])


class StatsResponse(BaseModel):
    active_count: int
    new_today_count: int
    avg_score_active: float | None = None
    last_crawl_at: str | None = None


@router.get("", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_session)) -> StatsResponse:
    active = await count_active(session)

    since = _utcnow_naive() - timedelta(hours=24)
    new_today = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Article)
                .where(Article.first_seen_at >= since)
            )
        ).scalar_one()
    )

    avg_row = (
        await session.execute(
            select(func.avg(Article.score)).where(Article.is_active.is_(True))
        )
    ).scalar_one()
    avg = round(float(avg_row), 2) if avg_row is not None else None

    last_seen = (
        await session.execute(select(func.max(Article.last_seen_at)))
    ).scalar_one()
    last_crawl_at = last_seen.isoformat() if last_seen else None

    return StatsResponse(
        active_count=active,
        new_today_count=new_today,
        avg_score_active=avg,
        last_crawl_at=last_crawl_at,
    )
