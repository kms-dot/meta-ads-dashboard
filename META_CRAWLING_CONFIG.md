# Meta 광고 크롤링 설정 (업데이트)

## 주요 변경 사항

### 1. 수집 개수 증가
- **이전**: 키워드당 50~100개
- **현재**: 키워드당 **150개**
- **목표**: 카테고리당 최소 **200개 고유 광고**

### 2. 중복 제거
- `ad_id` 기준으로 중복 제거
- `ad_library_url` 기준 fallback
- 전체 키워드에서 수집된 광고 중 고유 광고만 보존

### 3. 타임아웃 설정
- **키워드당 타임아웃**: **600초 (10분)**
- GitHub Actions 6시간 제한 내 완료 보장
- 평균 키워드 수: 10~15개
- 예상 총 소요 시간: 1.5~2.5시간

### 4. 필터링 강화
- ✅ **노출수 "적음" 필터링** (활성화)
- ✅ **종료된 광고 필터링** (활성화)
- 품질 높은 광고만 수집

### 5. 스크롤 설정 최적화
- **max_scrolls**: 50 → **100** (증가)
- **scroll_pause**: 2초 (유지)
- **page_load_timeout**: 10초 → **15초** (증가)

## 설정 파일

### `config/categories.json`
```json
{
  "settings": {
    "max_ads_per_query": 150,
    "timeout_per_query": 600,
    "min_ads_per_category": 200
  },
  "categories": {
    "뷰티디바이스": {
      "max_ads_per_query": 150,
      "timeout_per_query": 600
    },
    "건강기능식품": {
      "max_ads_per_query": 150,
      "timeout_per_query": 600
    }
  }
}
```

### `config/meta_selectors_final.json`
- **구조/텍스트 기반 XPath 셀렉터** 사용
- 클래스명 변경에 강건함
- 파싱 성공률: **100%** (테스트 완료)

## 크롤링 로직

### 1. 키워드 생성 전략
```python
# 제품 타입: 최대 8개
product_types[:8]

# 사용자 브랜드: 전체
user_brands

# 기능 키워드 조합: 3 x 2 = 6개
function_keywords[:3] x product_types[:2]

# 총 키워드 수: 약 10~20개
```

### 2. 중복 제거 로직
```python
seen_ad_ids = set()

for ad in ads:
    ad_id = ad.get('ad_id')
    if ad_id and ad_id not in seen_ad_ids:
        seen_ad_ids.add(ad_id)
        unique_ads.append(ad)
```

### 3. 필터링 순서
1. 광고 정보 추출
2. 중복 체크 (ad_library_url)
3. 노출수 "적음" 필터링
4. 종료된 광고 필터링
5. 데이터 저장

## 예상 성능

### 시나리오 1: 뷰티디바이스 카테고리
- **키워드 수**: 약 15개
- **키워드당 광고**: 150개 목표
- **중복률**: 약 30%
- **필터링**: 약 10%
- **예상 고유 광고**: 15 x 150 x 0.7 x 0.9 = **약 1,400개**
- **소요 시간**: 약 1.5시간

### 시나리오 2: 건강기능식품 카테고리
- **키워드 수**: 약 20개
- **키워드당 광고**: 150개 목표
- **중복률**: 약 40%
- **필터링**: 약 15%
- **예상 고유 광고**: 20 x 150 x 0.6 x 0.85 = **약 1,500개**
- **소요 시간**: 약 2시간

## 사용 방법

### 직접 키워드 지정
```python
from main_meta import crawl_meta_ads

queries = ["메디큐브", "EOA", "뷰티디바이스"]
result = crawl_meta_ads(
    queries,
    max_ads_per_query=150,
    timeout_per_query=600
)
```

### 카테고리 기반 크롤링
```python
from main_meta import main_with_categories

# config/categories.json 사용
main_with_categories()
```

## 파싱 성공률

테스트 결과 (2025-02-11):
- **광고주명**: 100% (20/20)
- **광고 ID**: 100% (20/20)
- **게재 시작일**: 100% (20/20)
- **썸네일**: 100% (20/20)
- **광고 텍스트**: 100% (100/20)
- **광고 링크**: 100% (20/20)
- **상태**: 100% (20/20)

## 주의사항

1. **타임아웃 준수**: 키워드당 10분 초과 시 자동 스킵
2. **중복 제거**: ad_id 없는 광고는 URL로 중복 체크
3. **필터링**: 노출수 적음, 종료된 광고 자동 제외
4. **로그 확인**: `meta_output/` 디렉토리에 상세 로그 저장

## 트러블슈팅

### 광고 수가 부족한 경우
- 키워드 추가: `product_types`, `user_brands` 확장
- max_scrolls 증가: 100 → 150
- 필터링 완화: `is_low_impression()` 비활성화 (신중하게)

### 타임아웃이 자주 발생하는 경우
- timeout_per_query 증가: 600 → 900초
- max_ads_per_query 감소: 150 → 100
- 키워드 수 감소

### 중복률이 높은 경우
- 키워드 다양성 증가
- 기능 키워드 조합 활용
- 브랜드 키워드 추가
