"""
크롤링 결과를 Excel 파일로 생성
"""

import json
import pandas as pd
from datetime import datetime

print("Excel 리포트 생성 중...")

# 데이터 로드
with open('meta_output/meta_all_categories_20260211_190018.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Excel 파일 생성
output_file = f'meta_output/Meta광고레퍼런스_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

    # 1. 요약 시트
    summary_data = []
    total_ads = 0
    total_advertisers = 0

    for cat_name, cat_data in data['results'].items():
        total_ads += cat_data['total_ads']
        analysis = cat_data.get('overall_analysis', {})
        summary = analysis.get('summary', {})
        unique_advertisers = summary.get('unique_advertisers', 0)
        total_advertisers += unique_advertisers

        summary_data.append({
            '카테고리': cat_name,
            '총 광고수': cat_data['total_ads'],
            '고유 광고주': unique_advertisers,
            '평균 라이브(일)': round(summary.get('avg_days_live', 0), 1),
            '목표': 200,
            '달성률(%)': round((cat_data['total_ads'] / 200) * 100, 0)
        })

    df_summary = pd.DataFrame(summary_data)
    df_summary.loc[len(df_summary)] = ['전체 합계', total_ads, total_advertisers, '-', '-', '-']
    df_summary.to_excel(writer, sheet_name='요약', index=False)

    # 2. 카테고리별 광고 데이터
    for cat_name, cat_data in data['results'].items():
        ads_data = []

        # 각 쿼리의 광고 수집
        results_by_query = cat_data.get('results_by_query', {})
        for query, query_result in results_by_query.items():
            ads = query_result.get('ads', [])
            for ad in ads:
                ads_data.append({
                    '키워드': query,
                    '광고주': ad.get('advertiser', ''),
                    '광고 텍스트': ad.get('ad_text', '')[:100],  # 100자까지만
                    '게재 일수': ad.get('days_live', 0),
                    '게재 시작일': ad.get('start_date', ''),
                    '노출수': ad.get('impression_text', ''),
                    '플랫폼': ', '.join(ad.get('platforms', [])),
                    '광고 라이브러리 URL': ad.get('ad_library_url', '')
                })

        if ads_data:
            df_ads = pd.DataFrame(ads_data)
            # 시트 이름 길이 제한 (31자)
            sheet_name = cat_name[:30]
            df_ads.to_excel(writer, sheet_name=sheet_name, index=False)

    # 3. 상위 광고주 시트
    top_advertisers_data = []
    for cat_name, cat_data in data['results'].items():
        analysis = cat_data.get('overall_analysis', {})
        advertiser_stats = analysis.get('advertiser_stats', [])

        for stat in advertiser_stats[:20]:  # 상위 20개
            top_advertisers_data.append({
                '카테고리': cat_name,
                '광고주': stat['advertiser'],
                '광고 개수': stat['ad_count'],
                '평균 게재일': round(stat.get('avg_days_live', 0), 1)
            })

    df_top = pd.DataFrame(top_advertisers_data)
    df_top = df_top.sort_values('광고 개수', ascending=False)
    df_top.to_excel(writer, sheet_name='상위광고주', index=False)

print(f"✅ Excel 파일 생성 완료: {output_file}")
print(f"\n시트 구성:")
print("1. 요약 - 카테고리별 통계")
print("2. 각 카테고리별 광고 상세 데이터")
print("3. 상위광고주 - 전체 TOP 광고주")
print(f"\n총 {total_ads:,}개 광고 데이터가 포함되었습니다.")
