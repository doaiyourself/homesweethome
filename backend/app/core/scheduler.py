"""APScheduler wiring — registered from the FastAPI lifespan.

Daily job runs `run_daily_crawl` at the configured KST hour:minute. The
Telegram push hook is wired in Phase 5; for now the job just commits and
logs the report.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.crawl_pipeline import run_daily_crawl
from app.services.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def daily_crawl_job() -> None:
    """Job executed by APScheduler — opens a fresh session, runs the pipeline,
    then pushes the new top-scoring listings to Telegram."""
    logger.info("Daily crawl job starting")
    settings = get_settings()
    async with SessionLocal() as session:
        try:
            report = await run_daily_crawl(session)
        except Exception:
            logger.exception("Daily crawl job failed")
            return
    logger.info(
        "Daily crawl finished: new=%d updated=%d deactivated=%d errors=%d avg=%s",
        report.new_count,
        report.updated_count,
        report.deactivated_count,
        report.error_count,
        report.average_score,
    )

    if not report.new_articles:
        logger.info("No new articles; skipping Telegram push")
        return

    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_ids=settings.telegram_chat_id_list,
        web_base_url=settings.web_base_url,
    )
    push_result = await notifier.send_new_articles(
        report.new_articles, min_score=settings.telegram_notify_min_score
    )
    logger.info(
        "Telegram push: sent=%d failed=%d skipped=%d",
        push_result.sent, push_result.failed, push_result.skipped,
    )


def start_scheduler() -> AsyncIOScheduler:
    """Create and start a singleton AsyncIOScheduler bound to the daily cron."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    settings = get_settings()
    _scheduler = AsyncIOScheduler(timezone=settings.crawl_timezone)
    _scheduler.add_job(
        daily_crawl_job,
        trigger=CronTrigger(
            hour=settings.crawl_schedule_hour,
            minute=settings.crawl_schedule_minute,
            timezone=settings.crawl_timezone,
        ),
        id="daily_crawl",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: daily_crawl at %02d:%02d %s",
        settings.crawl_schedule_hour,
        settings.crawl_schedule_minute,
        settings.crawl_timezone,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
