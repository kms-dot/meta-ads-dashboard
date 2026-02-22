import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 필터링된 데이터 로드
with open('meta_output/meta_all_categories_filtered_20260211_201256.json', encoding='utf-8') as f:
    data = json.load(f)

# Ultra Perfect 광고 찾기
print('=== Ultra Perfect 광고 찾기 ===\n')

all_ads = []
for category, cat_data in data['results'].items():
    for query, result in cat_data['results_by_query'].items():
        ads = result.get('ads', [])
        all_ads.extend(ads)

# Ultra Perfect 찾기
ultra_perfect = [ad for ad in all_ads if 'ultra perfect' in ad.get('advertiser', '').lower()]

if ultra_perfect:
    ad = ultra_perfect[0]
    print(f"광고주: {ad.get('advertiser')}")
    print(f"광고 텍스트: {ad.get('ad_text', '')[:100]}")
    print(f"\nthumbnail_url: {ad.get('thumbnail_url')}")
    print(f"ad_creative_image_url: {ad.get('ad_creative_image_url')}")
    print(f"video_url: {ad.get('video_url')}")
    print(f"media_type: {ad.get('media_type')}")
else:
    print("Ultra Perfect 광고를 찾을 수 없습니다.")

# 이미지 URL 통계
print('\n\n=== 이미지 URL 통계 ===\n')
no_thumbnail = 0
no_creative = 0
no_any_image = 0
has_video = 0

for ad in all_ads:
    thumb = ad.get('thumbnail_url')
    creative = ad.get('ad_creative_image_url')
    video = ad.get('video_url')
    
    if not thumb:
        no_thumbnail += 1
    if not creative:
        no_creative += 1
    if not thumb and not creative:
        no_any_image += 1
    if video:
        has_video += 1

print(f"총 광고 수: {len(all_ads)}개")
print(f"thumbnail_url 없음: {no_thumbnail}개 ({no_thumbnail/len(all_ads)*100:.1f}%)")
print(f"ad_creative_image_url 없음: {no_creative}개 ({no_creative/len(all_ads)*100:.1f}%)")
print(f"이미지 URL 둘 다 없음: {no_any_image}개 ({no_any_image/len(all_ads)*100:.1f}%)")
print(f"비디오 URL 있음: {has_video}개 ({has_video/len(all_ads)*100:.1f}%)")
