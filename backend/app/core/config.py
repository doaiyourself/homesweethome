"""Centralised settings loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database — async DSN for the app, sync DSN for Alembic.
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    admin_token: str = "change-me"

    # Crawler
    crawl_user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    crawl_min_sleep_sec: float = 1.0
    crawl_max_sleep_sec: float = 3.0
    crawl_schedule_hour: int = 9
    crawl_schedule_minute: int = 0
    crawl_timezone: str = "Asia/Seoul"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_ids: str = ""  # comma-separated
    telegram_notify_min_score: float = 70.0
    web_base_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    @property
    def telegram_chat_id_list(self) -> list[str]:
        return [c.strip() for c in self.telegram_chat_ids.split(",") if c.strip()]

    @property
    def sync_database_url(self) -> str:
        """Sync DSN derived from async DSN — used by Alembic."""
        url = self.database_url
        url = url.replace("sqlite+aiosqlite", "sqlite")
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
