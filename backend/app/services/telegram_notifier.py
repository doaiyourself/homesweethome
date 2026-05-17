"""Telegram push for newly-seen articles.

The class is thin on purpose: one network seam, `_send`, that tests can
replace. Cards are HTML (parse_mode=HTML), URL preview disabled so the
formatted card stays compact.

Top-N articles get one card each; anything beyond N collapses into a
single "N more in the web app" summary message with a link.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.models import Article

logger = logging.getLogger(__name__)

DEFAULT_TOP_N = 5
TELEGRAM_API = "https://api.telegram.org"

# Map raw code → human-readable Korean trade type used in cards.
_TRADE_NAMES: dict[str, str] = {
    "B1": "전세",
    "B2": "월세",
    "A1": "매매",
    "B3": "단기",
}


@dataclass
class NotifyResult:
    sent: int = 0
    failed: int = 0
    skipped: int = 0


class TelegramNotifier:
    def __init__(
        self,
        *,
        bot_token: str,
        chat_ids: list[str],
        web_base_url: str = "",
        top_n: int = DEFAULT_TOP_N,
        timeout: float = 10.0,
    ) -> None:
        self._bot_token = bot_token
        self._chat_ids = [c for c in chat_ids if c]
        self._web_base_url = web_base_url.rstrip("/")
        self._top_n = top_n
        self._timeout = timeout

    # ---- Public API --------------------------------------------------------

    async def send_message(
        self, chat_id: str, text: str, *, disable_preview: bool = True
    ) -> bool:
        return await self._send(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": disable_preview,
            }
        )

    async def send_new_articles(
        self,
        articles: list[Article],
        *,
        min_score: float | None = None,
    ) -> NotifyResult:
        """Send card-per-article (top N) and a tail summary."""
        result = NotifyResult()
        if not self._bot_token or not self._chat_ids:
            logger.info("Telegram not configured; skipping push")
            result.skipped = len(articles)
            return result

        filtered = [
            a for a in articles
            if min_score is None or (a.score is not None and a.score >= min_score)
        ]
        if not filtered:
            logger.info("No articles above min_score=%s; skipping push", min_score)
            return result

        # Highest-scoring first.
        filtered.sort(key=lambda a: (a.score or 0), reverse=True)
        head, tail = filtered[: self._top_n], filtered[self._top_n :]

        for chat_id in self._chat_ids:
            for article in head:
                ok = await self.send_message(chat_id, self._format_card(article))
                result.sent += int(ok)
                result.failed += int(not ok)
            if tail:
                ok = await self.send_message(
                    chat_id, self._format_tail_summary(len(tail))
                )
                result.sent += int(ok)
                result.failed += int(not ok)
        return result

    # ---- Formatting --------------------------------------------------------

    def _format_card(self, article: Article) -> str:
        trade_label = _TRADE_NAMES.get(article.trade_type or "", article.trade_type or "")
        price = self._format_price(article)

        floor_part = ""
        if article.floor_current and article.floor_total:
            floor_part = f" · {article.floor_current}/{article.floor_total}층"
        elif article.floor_current:
            floor_part = f" · {article.floor_current}층"

        area_part = f"{article.area_pyeong}평" if article.area_pyeong else ""

        lines: list[str] = []
        title = article.complex_name or article.building_name or article.article_no
        header = f"🏠 <b>{_esc(title)}</b>"
        if area_part or floor_part:
            header += f" · {_esc(area_part)}{_esc(floor_part)}"
        lines.append(header)

        if price:
            lines.append(f"💰 {_esc(trade_label)} {_esc(price)}")
        meta_bits: list[str] = []
        if article.direction:
            meta_bits.append(article.direction)
        if article.cp_name:
            meta_bits.append(article.cp_name)
        if meta_bits:
            lines.append(f"📍 {_esc(' · '.join(meta_bits))}")

        if article.score is not None:
            lines.append(f"⭐ 점수 {article.score:.1f}/100")

        if article.cp_article_url:
            lines.append(f'🔗 <a href="{_esc(article.cp_article_url)}">네이버 매물 보기</a>')
        if self._web_base_url:
            web_link = f"{self._web_base_url}/articles/{article.article_no}"
            lines.append(f'🌐 <a href="{_esc(web_link)}">웹에서 보기</a>')

        return "\n".join(lines)

    def _format_tail_summary(self, remaining: int) -> str:
        line = f"➕ <b>+{remaining}건 더 있음</b>"
        if self._web_base_url:
            return line + f'\n<a href="{_esc(self._web_base_url)}">웹에서 전체 보기</a>'
        return line

    def _format_price(self, article: Article) -> str:
        """Render deposit / monthly_rent into a Korean price label."""
        if article.price_display:
            base = article.price_display
        elif article.deposit:
            base = _format_man(article.deposit)
        else:
            base = ""
        if article.monthly_rent:
            return f"{base}/{article.monthly_rent}"
        return base

    # ---- Network seam (tests stub this) ------------------------------------

    async def _send(self, payload: dict[str, Any]) -> bool:
        url = f"{TELEGRAM_API}/bot{self._bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
        except httpx.HTTPError as e:
            logger.warning("Telegram send failed: %s", e)
            return False
        if resp.status_code != 200:
            logger.warning(
                "Telegram non-200: %s %s", resp.status_code, resp.text[:200]
            )
            return False
        return True


def _format_man(amount: int) -> str:
    """Render `만원` integers like 85000 → "8억 5,000" / 5000 → "5,000"."""
    if amount >= 10000:
        eok, man = divmod(amount, 10000)
        if man == 0:
            return f"{eok}억"
        return f"{eok}억 {man:,}"
    return f"{amount:,}"


def _esc(text: str) -> str:
    """Minimal HTML escape for Telegram parse_mode=HTML."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
