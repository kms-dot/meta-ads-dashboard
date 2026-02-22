"""
기존 4개 카테고리 + 새로운 건강기능식품 결과를 통합
"""

import json
from datetime import datetime

# 기존 4개 카테고리 결과 로드
with open('meta_output/meta_all_categories_20260211_173716.json', 'r', encoding='utf-8') as f:
    old_data = json.load(f)

# 새 건강기능식품 결과 로드
with open('meta_output/meta_건강기능식품_20260211_181121.json', 'r', encoding='utf-8') as f:
    health_food_data = json.load(f)

# 통합
old_data['results']['건강기능식품'] = health_food_data
old_data['crawl_date'] = datetime.now().isoformat()

# 저장
output_file = f'meta_output/meta_all_categories_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(old_data, f, ensure_ascii=False, indent=2)

print(f"✅ 통합 완료: {output_file}")
print(f"\n5개 카테고리 최종 결과:")
for cat_name, cat_data in old_data['results'].items():
    print(f"- {cat_name}: {cat_data['total_ads']}개")

total = sum(c['total_ads'] for c in old_data['results'].values())
print(f"\n총 합계: {total:,}개 광고")
