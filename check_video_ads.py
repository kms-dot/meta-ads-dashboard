import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 필터링된 데이터 로드
with open('meta_output/meta_all_categories_filtered_20260211_201256.json', encoding='utf-8') as f:
    data = json.load(f)

# DIVE 다이브 광고 찾기
print('=== DIVE 다이브 광고 찾기 ===\n')

all_ads = []
for category, cat_data in data['results'].items():
    for query, result in cat_data['results_by_query'].items():
        ads = result.get('ads', [])
        all_ads.extend(ads)

# DIVE 찾기
dive_ads = [ad for ad in all_ads if 'dive' in ad.get('advertiser', '').lower() or 'dive' in ad.get('ad_text', '').lower()]

if dive_ads:
    for i, ad in enumerate(dive_ads[:3], 1):
        print(f"\n--- 광고 {i} ---")
        print(f"광고주: {ad.get('advertiser')}")
        print(f"미디어 타입: {ad.get('media_type')}")
        print(f"thumbnail_url: {ad.get('thumbnail_url', 'None')[:100]}")
        print(f"ad_creative_image_url: {ad.get('ad_creative_image_url', 'None')[:100]}")
        print(f"video_url: {ad.get('video_url', 'None')[:100]}")
        print(f"video_preview_image_url: {ad.get('video_preview_image_url', 'None')[:100]}")
        
        # 모든 필드 확인
        for key in ad.keys():
            if 'image' in key.lower() or 'video' in key.lower() or 'thumb' in key.lower():
                print(f"{key}: {str(ad.get(key))[:100]}")

# 비디오 광고 통계
print('\n\n=== 미디어 타입별 통계 ===\n')
media_types = {}
for ad in all_ads:
    media_type = ad.get('media_type', 'unknown')
    media_types[media_type] = media_types.get(media_type, 0) + 1

for media_type, count in sorted(media_types.items(), key=lambda x: -x[1]):
    print(f"{media_type}: {count}개 ({count/len(all_ads)*100:.1f}%)")

# 이미지 없는 광고 샘플
print('\n\n=== 이미지 없는 광고 샘플 (처음 5개) ===\n')
no_image_ads = [ad for ad in all_ads if not ad.get('thumbnail_url') and not ad.get('ad_creative_image_url')]

for i, ad in enumerate(no_image_ads[:5], 1):
    print(f"\n{i}. 광고주: {ad.get('advertiser')}")
    print(f"   미디어 타입: {ad.get('media_type')}")
    print(f"   비디오 URL: {ad.get('video_url', 'None')[:80]}")
    
    # 모든 URL 필드 출력
    url_fields = [k for k in ad.keys() if 'url' in k.lower() or 'image' in k.lower()]
    for field in url_fields:
        value = ad.get(field, '')
        if value:
            print(f"   {field}: {str(value)[:80]}...")
