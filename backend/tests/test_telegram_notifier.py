"""Tests for TelegramNotifier — the `_send` seam is stubbed out so we never
make real HTTP calls."""
from __future__ import annotations

import pytest

from app.models import Article
from app.services.telegram_notifier import (
    TelegramNotifier,
    _format_man,
)


def make_article(**overrides) -> Article:
    a = Article(
        article_no=overrides.get("article_no", "A001"),
        complex_name=overrides.get("complex_name", "신도림SK뷰"),
        trade_type=overrides.get("trade_type", "B1"),
        deposit=overrides.get("deposit", 85000),
        monthly_rent=overrides.get("monthly_rent"),
        area_pyeong=overrides.get("area_pyeong", 25.7),
        floor_current=overrides.get("floor_current", "15"),
        floor_total=overrides.get("floor_total", 25),
        direction=overrides.get("direction", "남향"),
        score=overrides.get("score", 85.5),
        cp_article_url=overrides.get("cp_article_url"),
        tags=overrides.get("tags", []),
    )
    return a


class RecordingNotifier(TelegramNotifier):
    """Replaces the network seam with an in-memory log."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sent: list[dict] = []
        self.fail_next = False

    async def _send(self, payload):
        if self.fail_next:
            self.fail_next = False
            return False
        self.sent.append(payload)
        return True


def make_notifier(**kwargs) -> RecordingNotifier:
    defaults = dict(
        bot_token="fake-token",
        chat_ids=["111", "222"],
        web_base_url="https://app.example.com",
        top_n=3,
    )
    defaults.update(kwargs)
    return RecordingNotifier(**defaults)


def test_format_man():
    assert _format_man(85000) == "8억 5,000"
    assert _format_man(80000) == "8억"
    assert _format_man(5000) == "5,000"


def test_card_includes_key_fields():
    n = make_notifier()
    text = n._format_card(make_article())
    assert "신도림SK뷰" in text
    assert "25.7평" in text
    assert "15/25층" in text
    assert "전세" in text
    assert "8억 5,000" in text
    assert "남향" in text
    assert "85.5/100" in text


def test_card_handles_monthly():
    n = make_notifier()
    a = make_article(trade_type="B2", deposit=30000, monthly_rent=120)
    text = n._format_card(a)
    assert "월세" in text
    assert "3억/120" in text


def test_card_escapes_html():
    n = make_notifier()
    a = make_article(complex_name="<script>foo</script>")
    text = n._format_card(a)
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


@pytest.mark.asyncio
async def test_send_new_articles_sends_top_n_then_summary():
    n = make_notifier(top_n=2)
    articles = [
        make_article(article_no=f"A{i:03d}", score=90 - i * 5)
        for i in range(5)
    ]
    result = await n.send_new_articles(articles)
    # 2 chat_ids × (2 cards + 1 summary) = 6
    assert result.sent == 6
    assert result.failed == 0
    # All summaries reference the trailing 3
    summaries = [p for p in n.sent if "+3건" in p["text"]]
    assert len(summaries) == 2


@pytest.mark.asyncio
async def test_send_new_articles_no_tail_means_no_summary():
    n = make_notifier(top_n=5)
    articles = [make_article(article_no=f"A{i}", score=80) for i in range(3)]
    result = await n.send_new_articles(articles)
    # 2 chats × 3 cards = 6, no summary
    assert result.sent == 6
    assert not any("+0건" in p["text"] or "더 있음" in p["text"] for p in n.sent)


@pytest.mark.asyncio
async def test_send_new_articles_respects_min_score():
    n = make_notifier()
    articles = [
        make_article(article_no="A1", score=90),
        make_article(article_no="A2", score=60),
        make_article(article_no="A3", score=40),
    ]
    result = await n.send_new_articles(articles, min_score=70)
    # Only A1 above 70 → 1 card × 2 chat_ids
    assert result.sent == 2


@pytest.mark.asyncio
async def test_send_new_articles_skips_when_unconfigured():
    n = RecordingNotifier(bot_token="", chat_ids=[], web_base_url="")
    result = await n.send_new_articles([make_article()])
    assert result.sent == 0
    assert result.skipped == 1


@pytest.mark.asyncio
async def test_send_new_articles_orders_by_score_desc():
    n = make_notifier(top_n=2)
    articles = [
        make_article(article_no="LOW", score=50),
        make_article(article_no="HIGH", score=95),
        make_article(article_no="MID", score=70),
    ]
    # Send to only one chat to make assertion easier
    n._chat_ids = ["111"]
    await n.send_new_articles(articles)
    # First two cards should be HIGH, MID (top scored).
    card_texts = [p["text"] for p in n.sent if "+1건" not in p["text"]]
    # complex_name doesn't include article_no — check by score in the rendered card
    assert "95.0/100" in card_texts[0]
    assert "70.0/100" in card_texts[1]


@pytest.mark.asyncio
async def test_send_message_failure_returns_false():
    n = make_notifier()
    n.fail_next = True
    ok = await n.send_message("111", "hello")
    assert ok is False
