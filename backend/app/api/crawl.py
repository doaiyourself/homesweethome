"""/api/crawl/trigger — admin-token guarded manual crawl."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.services.crawl_pipeline import run_daily_crawl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


def _check_admin_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.admin_token or settings.admin_token == "change-me":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ADMIN_TOKEN not configured on the server.",
        )
    if x_admin_token != settings.admin_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin token.")


async def _run_crawl_in_background() -> None:
    """Open a fresh session and run the pipeline. Logs the report."""
    async with SessionLocal() as session:
        try:
            report = await run_daily_crawl(session)
        except Exception:
            logger.exception("Manual crawl failed")
            return
    logger.info(
        "Manual crawl finished: new=%d updated=%d deactivated=%d errors=%d avg=%s",
        report.new_count,
        report.updated_count,
        report.deactivated_count,
        report.error_count,
        report.average_score,
    )


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    _: None = Depends(_check_admin_token),
) -> dict[str, str]:
    background_tasks.add_task(_run_crawl_in_background)
    return {"status": "scheduled"}
