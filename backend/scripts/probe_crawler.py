"""Probe script: fetch 3 pages of articles from Sindorim and save the result.

Run from the backend/ directory:

    python -m scripts.probe_crawler

Outputs to ./data/probe_result.json. Prints a short summary to stdout.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Allow running as `python scripts/probe_crawler.py` from backend/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.crawler.constants import DEFAULT_REAL_ESTATE_TYPES, DEFAULT_TRADE_TYPES
from app.crawler.naver_client import NaverLandClient, NaverLandError
from app.crawler.parser import normalize_article_list
from app.crawler.regions import DONG_SINDORIM

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    user_agent = os.getenv("CRAWL_USER_AGENT", DEFAULT_UA)
    cortar_no = os.getenv("PROBE_CORTAR_NO", DONG_SINDORIM)
    pages = int(os.getenv("PROBE_PAGES", "3"))
    output_path = ROOT / "data" / "probe_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = NaverLandClient(user_agent=user_agent)

    try:
        client.fetch_token()
    except NaverLandError as e:
        print(f"[FAIL] token extraction failed: {e}", file=sys.stderr)
        print(
            "Hint: capture the actual request in Chrome DevTools and ask "
            "to swap in a Playwright-based token fetch.",
            file=sys.stderr,
        )
        return 2

    all_normalized: list[dict] = []
    raw_pages: list[dict] = []
    for page in range(1, pages + 1):
        try:
            payload = client.fetch_articles(
                cortar_no,
                trade_types=DEFAULT_TRADE_TYPES,
                real_estate_types=DEFAULT_REAL_ESTATE_TYPES,
                page=page,
            )
        except NaverLandError as e:
            print(f"[FAIL] page {page}: {e}", file=sys.stderr)
            return 3

        raw_pages.append({"page": page, "payload": payload})
        normalized = normalize_article_list(payload, cortar_no=cortar_no)
        all_normalized.extend(normalized)
        print(
            f"[page {page}] top-level keys={list(payload.keys())[:8]} "
            f"normalized_count={len(normalized)}"
        )

    output = {
        "cortar_no": cortar_no,
        "pages_fetched": pages,
        "article_count": len(all_normalized),
        "articles": all_normalized,
        "raw_pages": raw_pages,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"Wrote {output_path}")
    print(f"Total normalized articles: {len(all_normalized)}")
    if all_normalized:
        first = all_normalized[0]
        print()
        print("Sample (first article):")
        sample_keys = (
            "article_no",
            "complex_name",
            "trade_type",
            "deposit",
            "monthly_rent",
            "area_pyeong",
            "floor_current",
            "floor_total",
            "direction",
        )
        for k in sample_keys:
            print(f"  {k}: {first.get(k)!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
