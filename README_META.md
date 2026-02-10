# Meta 광고 라이브러리 크롤러

Meta(Facebook) 광고 라이브러리에서 광고 정보를 수집하고 분석하는 자동화 크롤링 시스템입니다.

## 주요 기능

- **CSS 변경 대응**: 다중 셀렉터 Fallback 전략으로 Meta의 CSS 변경에 대응
- **지능형 필터링**: 노출수 적음 광고 자동 필터링, 라이브 상태 확인
- **자동 스크롤**: 무한 스크롤 페이지 자동 탐색
- **광고 분석**: 광고주별, 미디어 타입별, 플랫폼별 통계 분석
- **라이브 일수 계산**: 게재 시작일로부터 현재까지 일수 자동 계산

## 프로젝트 구조

```
개발(1)/
├── config/
│   ├── categories.json          # 카테고리 설정
│   └── meta_selectors.json      # Meta 셀렉터 설정
├── meta_crawlers/
│   ├── __init__.py
│   ├── base_facebook_crawler.py # 기본 크롤러 클래스
│   └── meta_ad_library_crawler.py # Meta 광고 라이브러리 크롤러
├── meta_processors/
│   ├── __init__.py
│   └── ad_processor.py          # 광고 데이터 분석
├── meta_output/                 # 크롤링 결과 저장
├── main_meta.py                 # 메인 실행 스크립트
└── README_META.md
```

## 설치 방법

### 1. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- selenium >= 4.15.0
- webdriver-manager >= 4.0.0
- python-dotenv >= 1.0.0

### 2. 환경 변수 설정

`.env` 파일에서 설정 조정 (선택사항)

```bash
LOG_LEVEL=INFO
```

## 사용 방법

### 1. 기본 실행

```bash
python main_meta.py
```

기본적으로 다음 키워드로 크롤링합니다:
- 메디큐브
- EOA
- 뷰티디바이스
- 리프팅
- 피부관리기기

### 2. 키워드 커스터마이징

`main_meta.py` 파일에서 `queries` 리스트를 수정하세요:

```python
queries = [
    "메디큐브",
    "올리브영",
    "스킨케어"
]

result = crawl_meta_ads(queries, max_ads_per_query=100)
```

### 3. 카테고리 기반 크롤링

```python
# main_meta.py 파일 하단에서 주석 변경
if __name__ == "__main__":
    # main()  # 주석 처리
    main_with_categories()  # 활성화
```

## 핵심 기능 설명

### 1. CSS 변경 대응 전략

Meta는 로봇 접근을 감지하면 CSS 클래스명을 변경합니다. 이를 대응하기 위해 **다중 셀렉터 Fallback 전략**을 사용합니다.

```python
# config/meta_selectors.json
{
  "selectors": {
    "ad_card": [
      "div[class*='x1n2onr6']",              # CSS 클래스
      "div[data-testid='ad-card']",          # data 속성
      "div[aria-label*='광고']",             # aria-label
      "div.ad-card"                          # 구조 기반
    ]
  }
}
```

크롤러는 위에서부터 순차적으로 셀렉터를 시도하여 요소를 찾습니다.

### 2. 노출수 필터링

"노출수: 적음" 광고는 자동으로 제외됩니다:

```python
def is_low_impression(ad_card):
    # "적음", "low", "fewer" 등의 키워드 감지
    # True 반환 시 해당 광고 제외
```

### 3. 라이브 일수 계산

게재 시작일로부터 자동 계산:

```python
def calculate_days_live(start_date_text):
    # "2024년 12월 15일" -> 57일 (2026년 2월 10일 기준)
    # 한국어, 영어, ISO 형식 모두 지원
```

### 4. 광고 정보 추출

각 광고에서 다음 정보를 추출합니다:

```python
{
    'advertiser': str,           # 광고주
    'ad_id': str,                # 광고 ID
    'ad_text': str,              # 광고 텍스트
    'thumbnail_url': str,        # 썸네일 URL
    'video_url': str,            # 비디오 URL (있는 경우)
    'media_type': str,           # 'image', 'video', 'unknown'
    'ad_library_url': str,       # 광고 라이브러리 URL
    'start_date': str,           # 게재 시작일
    'days_live': int,            # 라이브 일수
    'platforms': list,           # ['Facebook', 'Instagram']
    'impression_text': str       # 노출수 정보
}
```

## 결과 데이터 구조

### 개별 쿼리 결과

```json
{
  "query": "메디큐브",
  "total_ads": 50,
  "crawl_date": "2026-02-10T12:00:00",
  "ads": [
    {
      "advertiser": "메디큐브 공식",
      "ad_id": "123456789",
      "ad_text": "메디큐브 에이지알 부스터...",
      "thumbnail_url": "https://...",
      "media_type": "video",
      "days_live": 45,
      "platforms": ["Facebook", "Instagram"]
    }
  ]
}
```

### 종합 분석 결과

```json
{
  "overall_analysis": {
    "summary": {
      "total_ads": 250,
      "unique_advertisers": 35,
      "avg_days_live": 42.5
    },
    "advertiser_stats": [
      {
        "advertiser": "메디큐브 공식",
        "ad_count": 15,
        "avg_days_live": 38.2,
        "media_types": {
          "video": 10,
          "image": 5
        }
      }
    ],
    "timeline_stats": {
      "very_recent": 50,    # 0-7일
      "recent": 80,         # 8-30일
      "medium": 70,         # 31-90일
      "long": 30,           # 91-180일
      "very_long": 20       # 181일+
    }
  }
}
```

## 크롤링 설정

### meta_selectors.json

```json
{
  "selectors": {
    "ad_card": [...],        # 광고 카드 셀렉터
    "advertiser": [...],     # 광고주 셀렉터
    "thumbnail": [...],      # 썸네일 셀렉터
    "impression": [...],     # 노출수 셀렉터
    "start_date": [...],     # 게재일 셀렉터
    "ad_link": [...]         # 광고 링크 셀렉터
  },
  "filter_keywords": {
    "low_impression": ["적음", "low"],
    "active_status": ["게재 중", "active"],
    "inactive_status": ["종료", "ended"]
  },
  "scroll_settings": {
    "max_scrolls": 50,       # 최대 스크롤 횟수
    "scroll_pause": 2,       # 스크롤 후 대기 시간(초)
    "max_retries": 3,        # 재시도 횟수
    "page_load_timeout": 10  # 페이지 로드 타임아웃(초)
  }
}
```

## 고급 사용법

### 1. 광고주별 필터링

```python
from meta_processors import AdProcessor

processor = AdProcessor()

# 특정 광고주만 추출
filtered_ads = processor.filter_by_advertiser(
    ads,
    advertisers=['메디큐브 공식', 'EOA']
)
```

### 2. 라이브 일수별 필터링

```python
# 30일 이상 라이브 중인 광고만
long_running_ads = processor.filter_by_days_live(
    ads,
    min_days=30
)

# 최근 7일 이내 광고만
recent_ads = processor.filter_by_days_live(
    ads,
    min_days=0,
    max_days=7
)
```

### 3. 미디어 타입별 필터링

```python
# 비디오 광고만
video_ads = processor.filter_by_media_type(
    ads,
    media_types=['video']
)
```

### 4. 플랫폼별 필터링

```python
# Instagram 광고만
instagram_ads = processor.filter_by_platform(
    ads,
    platforms=['Instagram']
)
```

## 문제 해결

### 1. 광고 카드를 찾을 수 없음

**원인**: Meta가 CSS 클래스를 변경했을 가능성

**해결**:
1. Chrome 개발자 도구로 실제 광고 카드 요소 확인
2. `config/meta_selectors.json`의 `ad_card` 셀렉터 업데이트

```json
{
  "selectors": {
    "ad_card": [
      "div[class*='새로운클래스명']",  // 추가
      "div[class*='x1n2onr6']",
      ...
    ]
  }
}
```

### 2. 페이지 로드 타임아웃

**원인**: 네트워크 속도 또는 Meta 서버 응답 지연

**해결**:
- `config/meta_selectors.json`에서 `page_load_timeout` 증가

```json
{
  "scroll_settings": {
    "page_load_timeout": 20  // 10 -> 20으로 증가
  }
}
```

### 3. 중복 광고 수집

**원인**: 스크롤 시 동일 광고가 다시 로드됨

**해결**: 이미 구현되어 있음 (광고 URL 기준 중복 제거)

### 4. 날짜 파싱 실패

**원인**: 예상하지 못한 날짜 형식

**해결**:
- `meta_selectors.json`의 `date_patterns`에 새 패턴 추가

```json
{
  "date_patterns": {
    "korean": "(?P<year>\\d{4})년...",
    "your_pattern": "새로운 정규식 패턴"
  }
}
```

## 주의사항

1. **로봇 배제 표준**: Meta 광고 라이브러리는 공개 데이터이지만, 과도한 요청은 피하세요
2. **속도 제한**: `scroll_pause` 설정으로 적절한 딜레이 유지
3. **IP 차단**: VPN 또는 프록시 사용 고려 (장시간 크롤링 시)
4. **데이터 사용**: 수집한 데이터의 저작권 및 이용 약관 확인

## 성능 최적화

### 1. 헤드리스 모드 활성화

`meta_crawlers/base_facebook_crawler.py`:

```python
def setup_driver(self):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 주석 해제
    ...
```

### 2. 병렬 크롤링

여러 키워드를 동시에 크롤링하려면 멀티프로세싱 사용:

```python
from multiprocessing import Pool

def crawl_single_query(query):
    with MetaAdLibraryCrawler(config) as crawler:
        return crawler.crawl(query)

queries = ['키워드1', '키워드2', '키워드3']

with Pool(3) as p:
    results = p.map(crawl_single_query, queries)
```

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
