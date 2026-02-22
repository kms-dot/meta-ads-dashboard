import json
import sys

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
with open('meta_output/meta_all_categories_20260211_190018.json', encoding='utf-8') as f:
    data = json.load(f)

skincare = data['results']['스킨케어']

print('=== 스킨케어 쿼리 키워드 ===')
for q in skincare['queries']:
    print(f'  - {q}')

print(f'\n총 광고 수: {skincare["total_ads"]}개\n')

# 각 쿼리별로 샘플 광고 확인
print('=== 각 쿼리별 샘플 광고 (처음 3개) ===')
for query, result in skincare['results_by_query'].items():
    print(f'\n[{query}] - {result["total_ads"]}개 광고')
    ads = result.get('ads', [])[:3]
    for i, ad in enumerate(ads, 1):
        advertiser = ad.get('advertiser', '알 수 없음')
        text = ad.get('ad_text', '')[:80].replace('\n', ' ')
        print(f'  {i}. {advertiser}: {text}...')
