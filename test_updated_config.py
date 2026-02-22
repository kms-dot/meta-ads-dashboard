"""
업데이트된 설정 테스트 스크립트

수정 사항:
1. 키워드당 최대 150개 광고 수집
2. 중복 제거 로직
3. 카테고리당 최소 200개 보장
4. 키워드당 타임아웃 10분
5. 노출수 "적음" 및 종료 광고 필터링
"""

import logging
from main_meta import crawl_meta_ads

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("="*60)
    print("업데이트된 설정 테스트")
    print("="*60)

    # 테스트용 키워드 (적은 수)
    queries = [
        "메디큐브",
        "EOA"
    ]

    print(f"\n테스트 키워드: {queries}")
    print(f"키워드당 최대 광고 수: 150개")
    print(f"키워드당 타임아웃: 600초 (10분)")
    print(f"필터링: 노출수 적음, 종료된 광고\n")

    # 크롤링 실행
    result = crawl_meta_ads(
        queries,
        max_ads_per_query=150,
        timeout_per_query=600
    )

    # 결과 출력
    print("\n" + "="*60)
    print("크롤링 결과")
    print("="*60)

    for query, data in result.get('results_by_query', {}).items():
        print(f"\n키워드: {query}")
        print(f"  수집된 광고: {data.get('total_ads', 0)}개")
        print(f"  중복 제거 후: {data.get('unique_ads', 0)}개")
        print(f"  소요 시간: {data.get('elapsed_seconds', 0):.1f}초")

    print(f"\n전체 통계:")
    print(f"  총 수집: {sum(d['total_ads'] for d in result.get('results_by_query', {}).values())}개")
    print(f"  중복 제거 후: {result.get('total_ads', 0)}개 (고유 광고)")

    # 필터링 통계
    analysis = result.get('overall_analysis', {})
    summary = analysis.get('summary', {})

    print(f"\n광고 품질:")
    print(f"  고유 광고주: {summary.get('unique_advertisers', 0)}개")
    print(f"  평균 라이브 일수: {summary.get('avg_days_live', 0):.1f}일")

    print("\n" + "="*60)
    print("테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    main()
