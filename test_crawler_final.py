"""
최종 크롤러 테스트

업데이트된 meta_ad_library_crawler를 실제로 테스트합니다.
"""

import sys
import logging
from meta_crawlers.meta_ad_library_crawler import MetaAdLibraryCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("="*60)
    print("최종 크롤러 테스트")
    print("="*60)

    # 크롤러 설정
    config = {
        'headless': False,  # 디버깅용 브라우저 표시
        'max_scrolls': 5,
        'scroll_pause': 2
    }

    try:
        # 크롤러 초기화
        print("\n크롤러 초기화 중...")
        crawler = MetaAdLibraryCrawler(config)

        # 검색 쿼리
        query = "메디큐브"
        max_ads = 20

        print(f"\n검색 쿼리: {query}")
        print(f"최대 광고 수: {max_ads}")

        # 크롤링 실행
        print("\n크롤링 시작...\n")
        ads_data = crawler.crawl(query, max_ads=max_ads)

        # 결과 출력
        print("\n" + "="*60)
        print("크롤링 결과")
        print("="*60)

        print(f"\n총 수집된 광고 수: {len(ads_data)}개")

        if ads_data:
            print("\n처음 5개 광고 정보:")
            print("-"*60)

            for i, ad in enumerate(ads_data[:5], 1):
                print(f"\n광고 #{i}")
                print(f"  광고주: {ad.get('advertiser', 'N/A')}")
                print(f"  광고 ID: {ad.get('ad_id', 'N/A')}")
                print(f"  광고 라이브러리 URL: {ad.get('ad_library_url', 'N/A')[:80]}...")
                print(f"  게재 시작일: {ad.get('start_date', 'N/A')}")
                print(f"  라이브 일수: {ad.get('days_live', 'N/A')}일")
                print(f"  상태: {ad.get('status', 'N/A')}")

                ad_text = ad.get('ad_text', 'N/A')
                if len(ad_text) > 50:
                    ad_text = ad_text[:50] + "..."
                try:
                    print(f"  광고 텍스트: {ad_text}")
                except UnicodeEncodeError:
                    print(f"  광고 텍스트: [인코딩 오류]")

                print(f"  썸네일 URL: {ad.get('thumbnail_url', 'N/A')[:60]}...")
                print(f"  플랫폼: {', '.join(ad.get('platforms', []))}")

            # 통계
            print("\n" + "-"*60)
            print("필드별 채워진 비율:")

            fields = ['advertiser', 'ad_id', 'start_date', 'thumbnail_url', 'ad_text', 'platforms']
            for field in fields:
                filled = sum(1 for ad in ads_data if ad.get(field))
                rate = (filled / len(ads_data)) * 100
                print(f"  {field}: {filled}/{len(ads_data)} ({rate:.1f}%)")

        print("\n" + "="*60)
        print("테스트 완료!")
        print("="*60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            crawler.close()
        except:
            pass

if __name__ == "__main__":
    main()
