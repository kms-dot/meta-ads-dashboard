# 쇼핑 플랫폼 크롤러

네이버 쇼핑, 쿠팡, 올리브영에서 제품 정보를 수집하고 브랜드 및 키워드 분석을 수행하는 자동화 크롤링 시스템입니다.

## 주요 기능

- **다중 플랫폼 크롤링**: 네이버 쇼핑, 쿠팡, 올리브영 지원
- **자동 키워드 생성**: 카테고리 설정을 기반으로 검색 키워드 자동 생성
- **브랜드 분석**: 상위 브랜드 추출 및 경쟁사 분석
- **키워드 분석**: 인기 키워드 추출 및 빈도 분석
- **결과 저장**: JSON 형식으로 크롤링 결과 저장

## 프로젝트 구조

```
개발(1)/
├── config/
│   └── categories.json          # 카테고리 및 크롤링 설정
├── crawlers/
│   ├── __init__.py
│   ├── base_crawler.py          # 크롤러 기본 클래스
│   ├── naver_crawler.py         # 네이버 쇼핑 크롤러
│   ├── coupang_crawler.py       # 쿠팡 크롤러
│   └── oliveyoung_crawler.py    # 올리브영 크롤러
├── processors/
│   ├── __init__.py
│   ├── keyword_cleaner.py       # 키워드 정제 및 추출
│   └── brand_extractor.py       # 브랜드 추출 및 분석
├── output/                      # 크롤링 결과 저장 폴더
├── .env.example                 # 환경 변수 예시
├── .gitignore
├── requirements.txt             # 의존성 패키지
├── main.py                      # 메인 실행 스크립트
└── README.md
```

## 설치 방법

### 1. Python 환경 설정

Python 3.8 이상이 필요합니다.

```bash
# 가상환경 생성 (선택사항)
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 설정을 수정합니다.

```bash
cp .env.example .env
```

## 사용 방법

### 1. 카테고리 설정

`config/categories.json` 파일에서 크롤링할 카테고리를 설정합니다.

```json
{
  "categories": {
    "뷰티디바이스": {
      "product_types": ["디바이스", "기기", "미용기기"],
      "function_keywords": [],
      "user_brands": ["EOA", "메디큐브"],
      "crawl_platforms": ["naver", "coupang", "oliveyoung"]
    }
  }
}
```

**주요 설정 항목:**
- `product_types`: 제품 유형 키워드
- `function_keywords`: 기능 관련 키워드
- `user_brands`: 분석할 특정 브랜드
- `crawl_platforms`: 크롤링할 플랫폼 선택
- `oliveyoung_url`: 올리브영 카테고리 URL (선택사항)

### 2. 크롤링 실행

```bash
python main.py
```

### 3. 결과 확인

크롤링 결과는 `output/` 폴더에 JSON 형식으로 저장됩니다.

**파일 종류:**
- `{카테고리명}_{날짜시간}.json`: 카테고리별 상세 결과
- `summary_{날짜시간}.json`: 전체 요약 결과
- `crawl_{날짜시간}.log`: 실행 로그

## 결과 데이터 구조

```json
{
  "category": "뷰티디바이스",
  "crawl_date": "2026-02-10T12:00:00",
  "search_keywords": ["디바이스", "미용기기"],
  "platforms": ["naver", "coupang"],
  "total_products": 500,
  "products": [
    {
      "name": "제품명",
      "brand": "브랜드명",
      "price": 100000,
      "review_count": 1234,
      "rating": 4.5,
      "platform": "naver",
      "keyword": "디바이스",
      "rank": 1
    }
  ],
  "brand_analysis": {
    "summary": {
      "total_products": 500,
      "user_brand_products": 50,
      "competitor_products": 450
    },
    "top_brands_by_count": [
      {
        "rank": 1,
        "brand": "메디큐브",
        "count": 50,
        "avg_rating": 4.5,
        "avg_price": 150000
      }
    ]
  },
  "top_keywords": [
    {"keyword": "리프팅", "count": 120},
    {"keyword": "모공", "count": 95}
  ]
}
```

## 주요 클래스

### Crawlers

- **BaseCrawler**: 모든 크롤러의 기본 클래스
  - Selenium 드라이버 설정
  - 공통 크롤링 메서드 제공

- **NaverShoppingCrawler**: 네이버 쇼핑 크롤러
- **CoupangCrawler**: 쿠팡 크롤러
- **OliveYoungCrawler**: 올리브영 크롤러

### Processors

- **KeywordCleaner**: 키워드 정제 및 추출
  - 제품명에서 키워드 추출
  - 불용어 제거
  - 검색 키워드 자동 생성

- **BrandExtractor**: 브랜드 추출 및 분석
  - 브랜드 정규화
  - 브랜드별 통계 계산
  - 경쟁사 분석

## 설정 옵션

### 크롤링 설정 (.env)

```bash
# 크롤링 딜레이 (초)
CRAWL_DELAY_MIN=3
CRAWL_DELAY_MAX=7

# 재시도 횟수
MAX_RETRY=3

# 키워드당 최대 제품 수
MAX_PRODUCTS_PER_KEYWORD=100

# 상위 브랜드 수
TOP_BRANDS_COUNT=50

# 로그 레벨
LOG_LEVEL=INFO
```

## 주의사항

1. **로봇 배제 표준 준수**: 각 사이트의 robots.txt를 확인하고 준수하세요.
2. **크롤링 속도**: 과도한 요청으로 인한 IP 차단을 방지하기 위해 적절한 딜레이를 설정하세요.
3. **법적 책임**: 수집한 데이터의 사용 목적과 범위를 확인하세요.
4. **Chrome 드라이버**: webdriver-manager가 자동으로 관리하므로 별도 설치 불필요합니다.

## 문제 해결

### Chrome 드라이버 오류
```bash
# webdriver-manager 재설치
pip install --upgrade webdriver-manager
```

### Selenium 오류
```bash
# Selenium 재설치
pip install --upgrade selenium
```

### 특정 플랫폼 크롤링 실패
- 웹사이트 구조 변경 가능성 확인
- CSS 선택자 업데이트 필요

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
