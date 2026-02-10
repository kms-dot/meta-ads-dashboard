# META 광고 레퍼런스 수집 시스템

완전 자동화된 Meta 광고 수집 및 분석 시스템입니다. 장기 라이브 광고를 찾아 성과 광고 인사이트를 제공합니다.

## 🎯 프로젝트 개요

### 목표

- Meta 광고 라이브러리에서 장기 라이브 광고 자동 수집
- 카테고리별 상위 브랜드 및 키워드 자동 추출
- 웹 대시보드를 통한 실시간 광고 레퍼런스 제공

### 주요 기능

1. **자동 키워드 수집** (월 1회)
   - 네이버 쇼핑, 쿠팡, 올리브영 크롤링
   - 상위 50개 브랜드 자동 추출
   - Supabase DB에 저장

2. **Meta 광고 크롤링** (매일 자동)
   - CSS 변경 대응 (다중 셀렉터 전략)
   - 노출수 적음 필터링
   - 라이브 일수 자동 계산
   - Supabase DB에 저장

3. **웹 대시보드** (Vercel 배포)
   - 카테고리별 필터링
   - 라이브 일수순 정렬
   - 반응형 디자인
   - Meta 광고 라이브러리 직접 연결

## 📁 프로젝트 구조

```
meta-ads-dashboard/
├── .github/workflows/          # GitHub Actions 자동화
│   ├── daily_crawl.yml        # 매일 자동 크롤링
│   └── monthly_keywords.yml   # 월간 키워드 갱신
│
├── config/                     # 설정 파일
│   ├── categories.json        # 카테고리 설정
│   └── meta_selectors.json    # Meta 셀렉터
│
├── crawlers/                   # 쇼핑몰 크롤러
│   ├── base_crawler.py
│   ├── naver_crawler.py
│   ├── coupang_crawler.py
│   └── oliveyoung_crawler.py
│
├── meta_crawlers/              # Meta 광고 크롤러
│   ├── base_facebook_crawler.py
│   └── meta_ad_library_crawler.py
│
├── processors/                 # 데이터 처리
│   ├── keyword_cleaner.py
│   └── brand_extractor.py
│
├── meta_processors/            # 광고 분석
│   └── ad_processor.py
│
├── database/                   # Supabase 연동
│   ├── schema.sql
│   ├── supabase_client.py
│   ├── ad_repository.py
│   ├── keyword_repository.py
│   ├── product_repository.py
│   └── crawl_log_repository.py
│
├── frontend/                   # Next.js 대시보드
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # 메인 페이지
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   └── AdCard.tsx     # 광고 카드
│   │   └── lib/
│   │       └── supabase.ts
│   └── package.json
│
├── main.py                     # 쇼핑몰 크롤링
├── main_meta.py                # Meta 크롤링
├── main_meta_db.py             # Meta 크롤링 + DB
├── update_keywords.py          # 키워드 자동 수집
│
├── requirements.txt
├── .env
└── README.md
```

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.10+
- Node.js 18+
- Supabase 계정
- GitHub 계정
- Vercel 계정 (선택사항)

### 2. 설치

#### 백엔드 (Python)

```bash
# 저장소 클론
git clone https://github.com/your-username/meta-ads-dashboard.git
cd meta-ads-dashboard

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

#### 프론트엔드 (Next.js)

```bash
cd frontend
npm install
```

### 3. 환경 변수 설정

#### 백엔드 `.env`

```env
# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# 로그 레벨
LOG_LEVEL=INFO
```

#### 프론트엔드 `.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 4. Supabase 데이터베이스 설정

1. Supabase 프로젝트 생성
2. SQL Editor에서 `database/schema.sql` 실행
3. 테이블 생성 확인

### 5. 키워드 초기화 (최초 1회)

```bash
python -c "
from database import KeywordRepository
import json

with open('config/categories.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

keyword_repo = KeywordRepository()

for category, data in config['categories'].items():
    keywords_dict = {
        'product_types': data.get('product_types', []),
        'brands': data.get('user_brands', []),
        'functions': data.get('function_keywords', [])
    }
    keyword_repo.save_keywords_batch(category, keywords_dict, 'user_provided')
    print(f'{category} 키워드 저장 완료')
"
```

### 6. 크롤링 실행

#### 쇼핑몰 크롤링

```bash
python main.py
```

#### Meta 광고 크롤링 + DB 저장

```bash
python main_meta_db.py
```

#### 키워드 자동 수집

```bash
python update_keywords.py
```

### 7. 대시보드 실행

```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:3000 열기

## 🤖 GitHub Actions 자동화

### 설정

1. GitHub Secrets 추가:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. 워크플로우 자동 실행:
   - **매일 00:00 (KST)**: Meta 광고 크롤링
   - **매월 1일 09:00 (KST)**: 키워드 갱신

### 수동 실행

1. GitHub > Actions
2. 워크플로우 선택
3. Run workflow 클릭

## 🌐 Vercel 배포

### 1. Vercel 프로젝트 생성

```bash
cd frontend
vercel
```

### 2. 환경 변수 설정

Vercel 대시보드:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 3. GitHub 자동 배포

1. Vercel > Add New Project
2. GitHub 저장소 선택
3. 환경 변수 설정
4. Deploy

**결과:**
- **main 브랜치 푸시** → 프로덕션 배포
- **다른 브랜치 푸시** → 프리뷰 배포

## 📊 시스템 아키텍처

```
┌─────────────────────────────────────────────┐
│          GitHub Actions                     │
│  ┌──────────────┐    ┌──────────────┐       │
│  │ Daily Crawl  │    │   Monthly    │       │
│  │   00:00 KST  │    │  Keyword     │       │
│  │              │    │  1st 09:00   │       │
│  └──────┬───────┘    └──────┬───────┘       │
└─────────┼────────────────────┼───────────────┘
          │                    │
          ▼                    ▼
┌─────────────────────────────────────────────┐
│              Python Backend                 │
│  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Meta Crawlers    │  │  E-commerce     │  │
│  │ - CSS Fallback   │  │  Crawlers       │  │
│  │ - Filter         │  │  - Naver        │  │
│  │ - Extract        │  │  - Coupang      │  │
│  └────────┬─────────┘  │  - OliveYoung   │  │
│           │            └─────────┬─────────┘  │
└───────────┼──────────────────────┼────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────┐
│          Supabase PostgreSQL                │
│  ┌──────┐  ┌──────────┐  ┌────────┐         │
│  │ ads  │  │ keywords │  │ brands │         │
│  └──────┘  └──────────┘  └────────┘         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      Next.js Frontend (Vercel)              │
│  ┌──────────────────────────────────────┐   │
│  │     Dashboard UI                     │   │
│  │  - Category Filter                   │   │
│  │  - Ad Cards                          │   │
│  │  - Stats                             │   │
│  │  - Responsive Design                 │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 📋 체크리스트

### 크롤링

- [x] 다중 셀렉터 전략 (CSS 변경 대응)
- [x] 노출수 "적음" 필터링
- [x] 라이브 광고만 수집
- [x] 게재 일수 자동 계산
- [x] 중복 광고 자동 제거

### 키워드

- [x] 사용자 제공 키워드 포함
- [x] 쇼핑몰 브랜드 자동 추출 (50개/카테고리)
- [x] 키워드 정제 (불용어 제거)
- [x] 카테고리당 60-100개 키워드 확보

### 데이터베이스

- [x] Supabase PostgreSQL 연동
- [x] 자동 중복 체크
- [x] 크롤링 이력 기록
- [x] 브랜드 통계 자동 갱신

### 자동화

- [x] 매일 자동 크롤링 (GitHub Actions)
- [x] 월간 키워드 갱신
- [x] 오래된 광고 자동 비활성화 (90일+)
- [x] 크롤링 결과 아티팩트 저장

### 대시보드

- [x] 카테고리별 필터
- [x] 라이브 일수순 정렬
- [x] 반응형 디자인
- [x] Meta 광고 라이브러리 연결
- [x] Vercel 배포

## 📈 예상 소요 시간

| 단계 | 작업 | 예상 시간 |
|------|------|-----------|
| Phase 1 | 키워드 수집 시스템 | 1-2일 |
| Phase 2 | Meta 크롤러 개발 | 2-3일 |
| Phase 3 | 데이터베이스 연동 | 1일 |
| Phase 4 | 프론트엔드 개발 | 2일 |
| Phase 5 | 자동화 & 배포 | 1-2일 |
| **총합** | | **7-10일** |

## 🛠️ 기술 스택

### 백엔드
- Python 3.10+
- Selenium + webdriver-manager
- Supabase Python SDK
- python-dotenv

### 프론트엔드
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Supabase JS SDK

### 인프라
- Supabase (PostgreSQL + Auth + Storage)
- GitHub Actions (CI/CD)
- Vercel (Frontend Hosting)

## 📚 문서

- [쇼핑몰 크롤러 가이드](README.md)
- [Meta 크롤러 가이드](README_META.md)
- [데이터베이스 연동](README_DATABASE.md)
- [자동화 가이드](README_AUTOMATION.md)
- [프론트엔드 가이드](frontend/README.md)

## 🔧 문제 해결

### 크롤링 실패

**증상:** CSS 선택자를 찾을 수 없음

**해결:** `config/meta_selectors.json`에 새 셀렉터 추가

### DB 연결 오류

**증상:** Supabase 환경 변수 오류

**해결:** `.env` 파일에 `SUPABASE_URL`, `SUPABASE_KEY` 확인

### 대시보드 빈 화면

**증상:** 광고가 표시되지 않음

**해결:**
1. Supabase에 데이터가 있는지 확인
2. 환경 변수 확인 (`NEXT_PUBLIC_` 접두사)
3. 브라우저 콘솔 에러 확인

## 📄 라이선스

MIT License

## 👥 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

---

**완전 자동화 Meta 광고 레퍼런스 수집 시스템** 🚀
