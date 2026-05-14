# 신혼집 매물 추천 (Naverland Recommender)

네이버 부동산에서 매일 매물을 크롤링해서 우리 조건에 맞는 매물을 추천하는 개인용 웹 서비스.

## 스펙

- **지역**: 서울 구로구, 양천구, 영등포구
- **거래**: 전세 + 월세
- **유형**: 아파트, 오피스텔, 빌라
- **자동화**: 매일 KST 09:00 크롤링 + 신규 매물 텔레그램 푸시
- **웹**: 매물 리스트, 지도, 찜/숨김, 사용자 설정

## 구조

```
HomeSweetHome/
├── backend/          # FastAPI + 크롤러 + 스케줄러
│   ├── app/
│   │   ├── api/      # 라우터
│   │   ├── core/     # 설정, DB, 스케줄러
│   │   ├── crawler/  # 네이버 크롤링
│   │   ├── models/   # SQLAlchemy 모델
│   │   ├── schemas/  # Pydantic
│   │   ├── services/ # 비즈니스 로직 (점수, 알림)
│   │   └── main.py
│   ├── tests/
│   ├── scripts/      # 수동 실행 스크립트 (probe, run_crawl)
│   ├── data/         # SQLite, 크롤링 결과
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/         # Next.js 14 (App Router) + TS + Tailwind
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 빠른 시작 (Phase 0)

이 단계에서는 골격만 있고 실제 동작 로직은 비어있다. 다음 단계 (Phase 1) 에서 크롤러부터 채운다.

### 1. 백엔드

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 필요한 값 채우기
uvicorn app.main:app --reload
```

`http://localhost:8000/health` 로 헬스체크 가능. `/docs` 에서 Swagger 확인.

### 2. 프론트엔드

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

`http://localhost:3000` 접속.

### 3. Docker Compose (Postgres 포함)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## 환경 변수

`backend/.env.example` 와 `frontend/.env.example` 참고. 주요 항목:

| 키 | 설명 |
|----|------|
| `DATABASE_URL` | SQLite (개발) 또는 Postgres (운영) |
| `ADMIN_TOKEN` | 수동 크롤 트리거 API 인증 |
| `TELEGRAM_BOT_TOKEN` | BotFather 토큰 |
| `TELEGRAM_CHAT_IDS` | 콤마 구분 chat id |
| `TELEGRAM_NOTIFY_MIN_SCORE` | 푸시할 최소 점수 (기본 70) |
| `CRAWL_SCHEDULE_HOUR` | 매일 크롤링 시각 (기본 9) |

## 로드맵

- [x] Phase 0 — 모노레포 골격
- [ ] Phase 1 — 네이버 크롤러 프로토타입 (probe 스크립트)
- [ ] Phase 2 — DB 모델 + 마이그레이션
- [ ] Phase 3 — 점수 계산 + 일 단위 파이프라인
- [ ] Phase 4 — FastAPI REST API
- [ ] Phase 5 — 텔레그램 봇
- [ ] Phase 6 — Next.js 프론트엔드
- [ ] Phase 7 — Railway / Vercel 배포

## 라이선스

개인 프로젝트.
