# Supabase 데이터베이스 연동 가이드

Meta 광고 및 쇼핑몰 크롤링 데이터를 Supabase PostgreSQL 데이터베이스에 저장하고 관리하는 시스템입니다.

## 목차

1. [Supabase 설정](#supabase-설정)
2. [데이터베이스 스키마](#데이터베이스-스키마)
3. [사용 방법](#사용-방법)
4. [API 레퍼런스](#api-레퍼런스)
5. [고급 활용](#고급-활용)

## Supabase 설정

### 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 접속하여 계정 생성
2. 새 프로젝트 생성
3. 프로젝트 설정에서 API 정보 확인

### 2. 데이터베이스 스키마 생성

Supabase 대시보드에서:

1. SQL Editor 메뉴로 이동
2. `database/schema.sql` 파일의 내용 복사
3. SQL 쿼리 실행

```bash
# 또는 로컬에서 실행 (psql 필요)
psql -h your-project.supabase.co -U postgres -d postgres -f database/schema.sql
```

### 3. 환경 변수 설정

`.env` 파일에 Supabase 정보 추가:

```bash
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**Supabase URL 및 Key 확인 방법:**
1. Supabase 프로젝트 대시보드 > Settings > API
2. Project URL → `SUPABASE_URL`
3. Project API keys > `anon` `public` → `SUPABASE_KEY`

### 4. Python 패키지 설치

```bash
pip install supabase
```

## 데이터베이스 스키마

### 테이블 구조

#### 1. `ads` - Meta 광고 데이터

```sql
CREATE TABLE ads (
    id UUID PRIMARY KEY,
    category VARCHAR(50),
    advertiser VARCHAR(200),
    ad_text TEXT,
    thumbnail_url TEXT,
    video_url TEXT,
    ad_library_url TEXT UNIQUE,  -- 중복 방지
    days_live INTEGER,
    start_date DATE,
    is_active BOOLEAN,
    collected_at TIMESTAMP
);
```

**주요 컬럼:**
- `ad_library_url`: 광고 고유 URL (중복 체크 기준)
- `days_live`: 광고 게재 시작일로부터 경과 일수
- `is_active`: 현재 라이브 중인지 여부

#### 2. `keywords` - 검색 키워드

```sql
CREATE TABLE keywords (
    id UUID PRIMARY KEY,
    category VARCHAR(50),
    keyword VARCHAR(200),
    keyword_type VARCHAR(20),  -- 'product_type', 'brand', 'function'
    source VARCHAR(50),
    search_priority INTEGER,
    search_count INTEGER,
    total_ads_found INTEGER,
    is_active BOOLEAN
);
```

**주요 컬럼:**
- `keyword_type`: 키워드 분류
- `search_priority`: 검색 우선순위 (높을수록 먼저 검색)
- `search_count`: 검색 실행 횟수

#### 3. `products` - 쇼핑몰 제품 데이터

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    category VARCHAR(50),
    name TEXT,
    brand VARCHAR(200),
    price INTEGER,
    review_count INTEGER,
    rating DECIMAL(3,2),
    platform VARCHAR(50),
    collected_at TIMESTAMP
);
```

#### 4. `crawl_logs` - 크롤링 이력

```sql
CREATE TABLE crawl_logs (
    id UUID PRIMARY KEY,
    crawl_type VARCHAR(20),  -- 'ecommerce', 'meta_ads'
    category VARCHAR(50),
    items_collected INTEGER,
    status VARCHAR(20),      -- 'success', 'failed', 'partial'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);
```

## 사용 방법

### 1. 키워드 DB 초기 설정

최초 1회 실행하여 `config/categories.json`의 키워드를 DB에 저장:

```python
from database import KeywordRepository

keyword_repo = KeywordRepository()

# 카테고리별 키워드 저장
keywords_dict = {
    'product_types': ['디바이스', '기기', '미용기기'],
    'brands': ['메디큐브', 'EOA'],
    'functions': ['리프팅', '탄력']
}

keyword_repo.save_keywords_batch(
    category='뷰티디바이스',
    keywords_dict=keywords_dict,
    source='user_provided'
)
```

**또는 메인 스크립트 사용:**

```python
# main_meta_db.py
if __name__ == "__main__":
    setup_keywords_in_db()  # 주석 해제 후 1회 실행
```

### 2. Meta 광고 크롤링 & DB 저장

```python
from database import AdRepository, CrawlLogRepository
from meta_crawlers import MetaAdLibraryCrawler

# Repository 초기화
ad_repo = AdRepository()
crawl_log_repo = CrawlLogRepository()

# 크롤링 로그 시작
log_id = crawl_log_repo.start_crawl_log(
    crawl_type='meta_ads',
    category='뷰티디바이스'
)

# 크롤링 실행
with MetaAdLibraryCrawler(config) as crawler:
    ads = crawler.crawl("메디큐브", max_ads=100)

# DB 저장
save_stats = ad_repo.save_ads_batch(ads, category='뷰티디바이스')

# 크롤링 로그 완료
crawl_log_repo.complete_crawl_log(
    log_id=log_id,
    items_collected=len(ads),
    items_new=save_stats['inserted'],
    status='success'
)
```

**간편 실행:**

```bash
python main_meta_db.py
```

### 3. DB에서 데이터 조회

```python
from database import AdRepository, KeywordRepository

ad_repo = AdRepository()
keyword_repo = KeywordRepository()

# 카테고리별 광고 조회
ads = ad_repo.get_ads_by_category('뷰티디바이스', limit=50)

# 활성 광고만 조회
active_ads = ad_repo.get_active_ads('뷰티디바이스')

# 라이브 일수 상위 광고
top_ads = ad_repo.get_top_ads_by_days_live('뷰티디바이스', limit=20)

# 광고주별 통계
stats = ad_repo.get_advertiser_stats('뷰티디바이스')

# 키워드 조회
keywords = keyword_repo.get_keywords_by_category('뷰티디바이스')
# 결과: {'product_types': [...], 'brands': [...], 'functions': [...]}
```

## API 레퍼런스

### AdRepository

#### `save_ad(ad_data: Dict, category: str) -> Dict`
광고 데이터 저장 (중복 시 자동 업데이트)

#### `save_ads_batch(ads: List[Dict], category: str) -> Dict`
여러 광고 일괄 저장

**반환값:**
```python
{
    'total': 100,
    'inserted': 95,
    'failed': 5
}
```

#### `get_active_ads(category: str = None) -> List[Dict]`
활성 광고 조회

#### `get_top_ads_by_days_live(category: str, limit: int) -> List[Dict]`
라이브 일수 상위 광고 조회

#### `get_advertiser_stats(category: str) -> List[Dict]`
광고주별 통계

**반환값:**
```python
[
    {
        'advertiser': '메디큐브',
        'ad_count': 15,
        'avg_days_live': 38.2,
        'active_ads': 10
    },
    ...
]
```

#### `deactivate_old_ads(days_threshold: int = 90) -> int`
오래된 광고 비활성화 (90일 이상)

### KeywordRepository

#### `save_keyword(category, keyword, keyword_type, source, priority) -> Dict`
단일 키워드 저장

#### `save_keywords_batch(category, keywords_dict, source) -> Dict`
여러 키워드 일괄 저장

**입력 형식:**
```python
keywords_dict = {
    'product_types': ['디바이스', '기기'],
    'brands': ['메디큐브', 'EOA'],
    'functions': ['리프팅', '탄력']
}
```

#### `get_active_keywords(category, keyword_type, limit) -> List[Dict]`
활성 키워드 조회

#### `get_keywords_by_category(category) -> Dict`
카테고리별 키워드 조회 (타입별 그룹화)

#### `update_search_stats(keyword_id, products_found, ads_found) -> Dict`
검색 통계 업데이트

#### `get_top_performing_keywords(category, metric, limit) -> List[Dict]`
성과 좋은 키워드 조회 (metric: 'products' or 'ads')

### CrawlLogRepository

#### `start_crawl_log(crawl_type, category, platform, query) -> str`
크롤링 시작 로그 생성

**반환값:** 로그 ID

#### `complete_crawl_log(log_id, items_collected, items_new, status) -> Dict`
크롤링 완료 로그 업데이트

#### `fail_crawl_log(log_id, error_message) -> Dict`
크롤링 실패 로그

#### `get_recent_logs(crawl_type, category, limit) -> List[Dict]`
최근 크롤링 로그 조회

#### `get_crawl_stats(crawl_type, days) -> Dict`
크롤링 통계 조회

**반환값:**
```python
{
    'total_crawls': 50,
    'success_crawls': 45,
    'failed_crawls': 5,
    'total_items_collected': 5000,
    'avg_duration_seconds': 120
}
```

## 고급 활용

### 1. DB에서 키워드 로드하여 크롤링

```python
from database import KeywordRepository

# DB에서 키워드 로드
keyword_repo = KeywordRepository()
keywords_dict = keyword_repo.get_keywords_by_category('뷰티디바이스')

# 브랜드 + 제품 타입 조합
queries = keywords_dict['brands'] + keywords_dict['product_types']

# 크롤링 실행
result = crawl_and_save_to_db(queries, '뷰티디바이스')
```

### 2. 정기 크롤링 & DB 자동 업데이트

```python
import schedule
import time

def daily_crawl():
    """매일 자동 크롤링"""
    categories = ['뷰티디바이스', '건강기능식품']

    for category in categories:
        # DB에서 키워드 로드
        queries = load_keywords_from_db(category)

        # 크롤링 및 DB 저장
        crawl_and_save_to_db(queries, category)

# 매일 오전 9시 실행
schedule.every().day.at("09:00").do(daily_crawl)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. 오래된 광고 정리

```python
from database import AdRepository

ad_repo = AdRepository()

# 90일 이상 된 광고 비활성화
deactivated_count = ad_repo.deactivate_old_ads(days_threshold=90)

print(f"{deactivated_count}개 광고 비활성화")
```

### 4. 광고주별 경쟁 분석

```python
from database import AdRepository

ad_repo = AdRepository()

# 카테고리별 광고주 통계
stats = ad_repo.get_advertiser_stats('뷰티디바이스')

# 상위 5개 광고주
top_advertisers = stats[:5]

for rank, stat in enumerate(top_advertisers, 1):
    print(f"{rank}. {stat['advertiser']}")
    print(f"   광고 수: {stat['ad_count']}")
    print(f"   평균 라이브 일수: {stat['avg_days_live']:.1f}일")
    print(f"   활성 광고: {stat['active_ads']}")
```

### 5. Supabase 대시보드에서 쿼리

Supabase SQL Editor에서 직접 쿼리 실행:

```sql
-- 카테고리별 활성 광고 통계
SELECT * FROM active_ads_stats;

-- 광고주별 광고 현황
SELECT * FROM brand_ads_summary
WHERE category = '뷰티디바이스'
LIMIT 20;

-- 최근 7일간 크롤링 통계
SELECT
    category,
    COUNT(*) as crawl_count,
    SUM(items_collected) as total_items
FROM crawl_logs
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY category;

-- 브랜드 통계 갱신 (수동 실행)
SELECT refresh_brand_stats();
```

## 문제 해결

### 1. Supabase 연결 오류

**증상:** `ValueError: Supabase 환경 변수가 설정되지 않았습니다`

**해결:**
1. `.env` 파일에 `SUPABASE_URL`과 `SUPABASE_KEY` 확인
2. 환경 변수가 올바르게 로드되는지 확인

```python
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv('SUPABASE_URL'))  # None이 아니어야 함
```

### 2. 중복 키 오류

**증상:** `duplicate key value violates unique constraint`

**원인:** `ad_library_url`이 이미 존재

**해결:** `AdRepository.save_ad()`는 자동으로 중복 체크 및 업데이트 수행. 직접 INSERT하지 말고 Repository 사용.

### 3. 날짜 파싱 실패

**증상:** `start_date`가 None으로 저장됨

**해결:** `AdRepository._parse_date()`가 다양한 형식 지원. 새로운 형식이 있다면 메서드 수정.

### 4. 대량 데이터 저장 시 느림

**해결:** `save_ads_batch()` 사용 또는 Supabase Bulk Insert 고려

```python
# 개선된 일괄 저장
ad_repo.save_ads_batch(ads, category)  # 내부적으로 순차 저장

# 또는 Supabase bulk insert (직접 구현 필요)
# self.client.table('ads').insert(ads_list).execute()
```

## 보안 주의사항

1. **API Key 보호**: `.env` 파일을 절대 Git에 커밋하지 마세요
2. **Row Level Security (RLS)**: Supabase에서 RLS 설정 권장
3. **API Key 권한**: `anon` 키는 읽기 전용으로 제한 권장

## 라이선스

MIT License
