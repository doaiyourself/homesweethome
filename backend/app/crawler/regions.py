"""Region codes (cortarNo) for the gus we care about, plus a cache builder.

Naver's cortarNo is a 10-digit hierarchical code:
    XXYYZZNNNN
    - first 2: 시도 (Seoul = 11)
    - next 3: 시군구
    - next 3: 읍면동
    - last 2: reserved (always 00)

Gu-level codes end with five trailing zeros. Dong-level codes are full 10
digits with no trailing zeros (typically).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .naver_client import NaverLandClient

logger = logging.getLogger(__name__)

# Gu-level cortarNo (구 단위)
GU_GURO = "1153000000"
GU_YANGCHEON = "1147000000"
GU_YEONGDEUNGPO = "1156000000"

TARGET_GUS: dict[str, str] = {
    "구로구": GU_GURO,
    "양천구": GU_YANGCHEON,
    "영등포구": GU_YEONGDEUNGPO,
}

# Well-known dong-level codes (for quick probing without going through
# regions/list). Sindorim is given as the example in the spec.
DONG_SINDORIM = "1153010100"


def build_region_cache(
    client: NaverLandClient,
    *,
    output_path: Path,
    gus: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch dong-level cortarNos for each target gu and persist to disk.

    Returns the cache dict and writes it as JSON.
    """
    gus = gus or TARGET_GUS
    cache: dict[str, Any] = {"gus": {}}

    for gu_name, gu_code in gus.items():
        logger.info("Fetching dongs for %s (%s)", gu_name, gu_code)
        payload = client.fetch_regions(gu_code)
        cache["gus"][gu_name] = {"cortarNo": gu_code, "raw": payload}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote region cache to %s", output_path)
    return cache


def load_region_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
