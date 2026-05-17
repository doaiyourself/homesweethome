"""Manually run one daily crawl cycle.

Usage (from backend/):
    python scripts/run_crawl.py

Requires the DB to be migrated (`alembic upgrade head`) and the UserPref
singleton to have `region_codes` populated. If region_codes is empty the
script seeds Guro / Yangcheon / Yeongdeungpo gu-level codes for you.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.crawler.regions import GU_GURO, GU_YANGCHEON, GU_YEONGDEUNGPO
from app.services.crawl_pipeline import run_daily_crawl
from app.services.user_pref_repository import get_or_create_pref


async def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = get_settings()
    print(f"DATABASE_URL = {settings.database_url}")

    async with SessionLocal() as session:
        pref = await get_or_create_pref(session)
        if not pref.region_codes:
            print("Seeding default region codes (Guro / Yangcheon / Yeongdeungpo)")
            pref.region_codes = [GU_GURO, GU_YANGCHEON, GU_YEONGDEUNGPO]
            await session.commit()

        report = await run_daily_crawl(session)

    print()
    print("=== Crawl report ===")
    print(f"  new        : {report.new_count}")
    print(f"  updated    : {report.updated_count}")
    print(f"  deactivated: {report.deactivated_count}")
    print(f"  errors     : {report.error_count}")
    print(f"  avg score  : {report.average_score}")
    for cortar_no, stats in report.per_region.items():
        print(f"  region {cortar_no}: {stats}")
    return 0 if report.error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
