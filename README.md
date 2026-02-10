# META 광고 레퍼런스 수집 시스템

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Next.js](https://img.shields.io/badge/next.js-14-black)
![License](https://img.shields.io/badge/license-MIT-green)

완전 자동화된 Meta 광고 수집 및 분석 시스템입니다. 장기 라이브 광고를 찾아 성과 광고 인사이트를 제공합니다.

## 🎯 핵심 기능

### 1. 자동 키워드 수집 (월 1회)
- 네이버 쇼핑, 쿠팡, 올리브영에서 자동으로 상위 브랜드 추출
- 카테고리당 50-100개 키워드 자동 생성
- Supabase DB에 자동 저장

### 2. Meta 광고 크롤링 (매일 자동)
- CSS 변경 대응 (다중 셀렉터 Fallback 전략)
- 노출수 "적음" 광고 자동 필터링
- 라이브 일수 자동 계산
- 중복 광고 자동 제거

### 3. 웹 대시보드 (24/7 접속 가능)
- 카테고리별 필터링
- 라이브 일수순 정렬
- 반응형 디자인 (PC/모바일)
- Meta 광고 라이브러리 직접 연결

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

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/meta-ads-dashboard.git
cd meta-ads-dashboard
```

### 2. 백엔드 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 Supabase 정보 입력
```

### 3. 프론트엔드 설정

```bash
cd frontend
npm install

# 환경 변수 설정
cp .env.example .env.local
# .env.local 파일에 Supabase 정보 입력
```

### 4. Supabase 데이터베이스 설정

1. [Supabase](https://supabase.com)에서 프로젝트 생성
2. SQL Editor에서 `database/schema.sql` 실행
3. API 정보를 환경 변수에 입력

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

```bash
# Meta 광고 크롤링
python main_meta_db.py

# 키워드 자동 수집
python update_keywords.py
```

### 7. 대시보드 실행

```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:3000 접속

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
├── database/                   # Supabase 연동
│   ├── schema.sql
│   ├── supabase_client.py
│   ├── ad_repository.py
│   ├── keyword_repository.py
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
└── requirements.txt            # Python 의존성
```

## 🤖 자동화

### GitHub Actions

저장소에 푸시하면 자동으로 활성화됩니다:

- **매일 00:00 (KST)**: Meta 광고 크롤링
- **매월 1일 09:00 (KST)**: 키워드 갱신

#### 수동 실행

1. GitHub > Actions 탭
2. 워크플로우 선택
3. "Run workflow" 클릭

#### Secrets 설정 (필수)

GitHub 저장소 > Settings > Secrets and variables > Actions

- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_KEY`: Supabase Anon Key

## 🌐 Vercel 배포

### CLI 배포 (추천)

```bash
cd frontend
npm install -g vercel
vercel login
vercel
```

### GitHub 연동 배포

1. [Vercel](https://vercel.com) 접속
2. "New Project" 클릭
3. GitHub 저장소 연동
4. Root Directory를 `frontend`로 설정
5. 환경 변수 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
6. "Deploy" 클릭

## 📚 문서

- [배포 체크리스트](DEPLOYMENT_CHECKLIST.md) - 단계별 배포 가이드
- [Meta 크롤러 가이드](README_META.md) - 크롤러 상세 설명
- [데이터베이스 연동](README_DATABASE.md) - DB 스키마 및 API
- [자동화 가이드](README_AUTOMATION.md) - GitHub Actions 설정
- [프론트엔드 가이드](frontend/README.md) - Next.js 개발 가이드
- [다음 단계](NEXT_STEPS.md) - 배포 후 작업
- [현재 상태](STATUS.md) - 프로젝트 현황

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

## 📊 데이터베이스 스키마

### 주요 테이블

- **ads**: Meta 광고 데이터 (광고주, 라이브 일수, 미디어 타입 등)
- **keywords**: 검색 키워드 (브랜드, 제품 타입, 기능 키워드)
- **products**: 쇼핑몰 제품 데이터
- **crawl_logs**: 크롤링 이력
- **brands**: 브랜드 통계

자세한 스키마는 [README_DATABASE.md](README_DATABASE.md) 참조

## 🔧 주요 설정

### 크롤링 설정 (`.env`)

```env
CRAWL_DELAY_MIN=3          # 최소 딜레이 (초)
CRAWL_DELAY_MAX=7          # 최대 딜레이 (초)
MAX_RETRY=3                # 재시도 횟수
MAX_PRODUCTS_PER_KEYWORD=100  # 키워드당 최대 제품 수
TOP_BRANDS_COUNT=50        # 상위 브랜드 수
LOG_LEVEL=INFO             # 로그 레벨
```

### 카테고리 설정 (`config/categories.json`)

```json
{
  "categories": {
    "뷰티디바이스": {
      "product_types": ["디바이스", "기기"],
      "function_keywords": ["리프팅", "탄력"],
      "user_brands": ["메디큐브", "EOA"],
      "crawl_platforms": ["naver", "coupang", "oliveyoung"]
    }
  }
}
```

## 🎨 대시보드 기능

### 필터 및 정렬
- 카테고리별 필터링
- 라이브 일수순 정렬
- 최신순 정렬

### 광고 카드
- 썸네일/비디오 미리보기
- 라이브 일수 배지
- 광고주 정보
- 플랫폼 아이콘
- 게재 시작일

### 통계
- 총 광고 수
- 광고주 수
- 평균 라이브 일수
- 비디오/이미지 광고 수

## 📈 성능 최적화

### 크롤링 최적화
- 헤드리스 모드 사용
- 적절한 딜레이 설정
- 중복 광고 자동 제거

### 대시보드 최적화
- Next.js 정적 생성 (SSG)
- Vercel Edge Network
- Tailwind CSS 최적화

### 데이터베이스 최적화
- 인덱스 설정 (ad_library_url, category, days_live)
- Materialized View (브랜드 통계)
- 90일 이상 광고 자동 비활성화

## 🔒 보안

### 환경 변수
- `.env` 파일은 Git에 커밋되지 않음 (.gitignore)
- GitHub Secrets로 관리
- Vercel 환경 변수로 관리

### API 키
- Supabase Anon Key 사용 (공개 가능)
- 서비스 키는 절대 노출하지 않음
- Row Level Security (RLS) 권장

### 크롤링
- 적절한 딜레이 설정
- robots.txt 준수
- User-Agent 설정

## 📊 사용량 제한

### GitHub Actions (무료 플랜)
- Public 저장소: 무제한
- Private 저장소: 월 2,000분

### Vercel (Hobby 플랜)
- 대역폭: 월 100GB
- 빌드 시간: 월 100시간
- 함수 실행: 일 100,000회

### Supabase (무료 플랜)
- DB 크기: 500MB
- 대역폭: 월 2GB
- API 요청: 제한 없음

## 🐛 문제 해결

### 크롤링 실패
- Chrome/ChromeDriver 버전 확인
- Supabase 연결 테스트
- CSS 셀렉터 업데이트 (`config/meta_selectors.json`)

### 대시보드 빈 화면
- Supabase에 데이터 존재 확인
- 환경 변수 확인 (`NEXT_PUBLIC_` 접두사)
- 브라우저 콘솔 에러 확인

### GitHub Actions 타임아웃
- `timeout-minutes` 증가
- 크롤링할 광고 수 줄이기
- 카테고리를 나눠서 실행

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

## 📄 라이선스

MIT License

---

**완전 자동화 Meta 광고 레퍼런스 수집 시스템** 🚀

배포 가이드: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
