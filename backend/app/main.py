"""FastAPI entrypoint."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import articles, crawl, prefs, stats
from app.core.config import get_settings
from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Scheduler is the cron driver in production; skip it under tests to keep
    # the event loop quiet.
    if not os.getenv("DISABLE_SCHEDULER"):
        start_scheduler()
    try:
        yield
    finally:
        if not os.getenv("DISABLE_SCHEDULER"):
            stop_scheduler()


app = FastAPI(title="Naverland Recommender", version="0.0.4", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(prefs.router)
app.include_router(crawl.router)
app.include_router(stats.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
