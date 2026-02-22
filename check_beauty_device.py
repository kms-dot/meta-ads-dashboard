import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 데이터 로드
with open('meta_output/meta_all_categories_filtered_20260211_200523.json', encoding='utf-8') as f:
    data = json.load(f)

beauty_device = data['results']['뷰티디바이스']

print('=== 뷰티디바이스 샘플 광고 (처음 20개) ===\n')
all_ads = []
for query, result in beauty_device['results_by_query'].items():
    ads = result.get('ads', [])
    all_ads.extend(ads)

for i, ad in enumerate(all_ads[:20], 1):
    advertiser = ad.get('advertiser', '알 수 없음')
    text = ad.get('ad_text', '')[:150].replace('\n', ' ')
    print(f'{i}. [{advertiser}]')
    print(f'   {text}...\n')
