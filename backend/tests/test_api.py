"""End-to-end API tests using FastAPI's TestClient over an in-memory SQLite.

Strategy:
    - Build a one-off async engine bound to file-backed SQLite in tempdir
      (in-memory sqlite breaks across the multiple connections FastAPI opens).
    - Override the `get_session` dependency to yield sessions from that engine.
    - Disable the scheduler so the test event loop stays clean.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DISABLE_SCHEDULER"] = "1"
os.environ["ADMIN_TOKEN"] = "test-admin-token"

from app.api.deps import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.article_repository import upsert_article  # noqa: E402
from app.services.user_pref_repository import update_pref  # noqa: E402


@pytest_asyncio.fixture
async def db_setup() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    dsn = f"sqlite+aiosqlite:///{tmp.name}"
    engine = create_async_engine(dsn, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield Maker
    await engine.dispose()
    Path(tmp.name).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def client(db_setup) -> AsyncIterator[TestClient]:
    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with db_setup() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_articles(db_setup):
    """Insert 3 articles with varying scores."""
    async with db_setup() as s:
        for i, score in enumerate([90.0, 75.0, 50.0], start=1):
            await upsert_article(
                s,
                {
                    "article_no": f"A00{i}",
                    "complex_name": f"단지{i}",
                    "trade_type": "B1",
                    "real_estate_type": "APT",
                    "deposit": 50000 + i * 1000,
                    "area_pyeong": 25.0,
                    "cortar_no": "1153010100",
                    "tags": ["역세권"],
                    "raw_data": None,
                    "score": score,
                },
            )
        await s.commit()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_articles_default_sort_by_score(client, seed_articles):
    r = client.get("/api/articles")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert [a["article_no"] for a in body["items"]] == ["A001", "A002", "A003"]
    assert body["items"][0]["score"] == 90.0


def test_list_articles_min_score(client, seed_articles):
    r = client.get("/api/articles?min_score=80")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_get_article_detail(client, seed_articles):
    r = client.get("/api/articles/A001")
    assert r.status_code == 200
    assert r.json()["article_no"] == "A001"


def test_get_article_detail_404(client, seed_articles):
    r = client.get("/api/articles/MISSING")
    assert r.status_code == 404


def test_favorite_flow(client, seed_articles):
    # Initially no favorites
    r = client.get("/api/articles/favorites")
    assert r.status_code == 200
    assert r.json()["total"] == 0

    # Add favorite
    r = client.post("/api/articles/A001/favorite")
    assert r.status_code == 204

    # Now appears in favorites and is annotated on detail
    r = client.get("/api/articles/favorites")
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["article_no"] == "A001"
    assert body["items"][0]["is_favorited"] is True

    r = client.get("/api/articles/A001")
    assert r.json()["is_favorited"] is True

    # Remove
    r = client.delete("/api/articles/A001/favorite")
    assert r.status_code == 204
    r = client.get("/api/articles/favorites")
    assert r.json()["total"] == 0


def test_hide_filters_from_default_list(client, seed_articles):
    client.post("/api/articles/A001/hide")
    r = client.get("/api/articles")
    body = r.json()
    assert body["total"] == 2
    assert "A001" not in [a["article_no"] for a in body["items"]]

    # show_hidden=true brings it back
    r = client.get("/api/articles?show_hidden=true")
    assert r.json()["total"] == 3


def test_prefs_default_get(client):
    r = client.get("/api/prefs")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert "price_fit" in body["weights"]


def test_prefs_update(client):
    body = {
        "region_codes": ["1153010100"],
        "deposit_max": 80000,
        "must_have_keywords": ["역세권"],
    }
    r = client.put("/api/prefs", json=body)
    assert r.status_code == 200
    assert r.json()["deposit_max"] == 80000

    # GET reflects the change
    r = client.get("/api/prefs")
    assert r.json()["deposit_max"] == 80000


def test_stats(client, seed_articles):
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["active_count"] == 3
    assert body["avg_score_active"] is not None


def test_crawl_trigger_requires_token(client):
    r = client.post("/api/crawl/trigger")
    assert r.status_code == 401


def test_crawl_trigger_accepts_with_token(client, monkeypatch):
    # Stub the background runner so we don't actually hit Naver
    from app.api import crawl as crawl_mod
    called = {"n": 0}

    async def _stub() -> None:
        called["n"] += 1

    monkeypatch.setattr(crawl_mod, "_run_crawl_in_background", _stub)
    r = client.post(
        "/api/crawl/trigger", headers={"X-Admin-Token": "test-admin-token"}
    )
    assert r.status_code == 202
    assert r.json() == {"status": "scheduled"}
