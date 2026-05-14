"""Constants for Naver Real Estate API.

Trade type codes:
    A1 = 매매, B1 = 전세, B2 = 월세, B3 = 단기임대

Real estate type codes (subset we care about):
    APT  = 아파트
    OPST = 오피스텔
    VL   = 빌라
    OR   = 원룸
    DDDGG = 단독/다가구
"""

# Trade types
TRADE_JEONSE = "B1"
TRADE_WOLSE = "B2"

DEFAULT_TRADE_TYPES = [TRADE_JEONSE, TRADE_WOLSE]

# Real estate types
REAL_ESTATE_APT = "APT"
REAL_ESTATE_OPST = "OPST"
REAL_ESTATE_VL = "VL"

DEFAULT_REAL_ESTATE_TYPES = [REAL_ESTATE_APT, REAL_ESTATE_OPST, REAL_ESTATE_VL]

# API base.
# As of May 2026 the modern frontend lives at neo.land.naver.com ("네이버페이
# 부동산 우리집"). The old new.land.naver.com HTML is dead (returns /404 shell),
# but its /api/* endpoints still resolve — they just rate-limit more aggressively.
# neo.land.naver.com serves both the page that carries the bearer token (in a
# <input id="token" data-token="..."> element) and the /api/articles endpoint.
NAVER_LAND_BASE = "https://neo.land.naver.com"
NAVER_LAND_API = f"{NAVER_LAND_BASE}/api"

# Default headers (Authorization filled in dynamically)
DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"{NAVER_LAND_BASE}/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}
