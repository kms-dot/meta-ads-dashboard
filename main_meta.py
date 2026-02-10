import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from meta_crawlers import MetaAdLibraryCrawler
from meta_processors import AdProcessor


# 환경 변수 로드
load_dotenv()


def setup_logging():
    """로깅 설정"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    # 로그 디렉토리 생성
    os.makedirs('meta_output', exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f'meta_output/meta_crawl_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )


def save_results(data: Dict, filename: str):
    """결과 저장"""
    os.makedirs('meta_output', exist_ok=True)

    filepath = os.path.join('meta_output', filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"결과 저장 완료: {filepath}")


def crawl_meta_ads(queries: List[str], max_ads_per_query: int = 100, country: str = 'KR') -> Dict:
    """
    Meta 광고 라이브러리 크롤링

    Args:
        queries: 검색 키워드 리스트
        max_ads_per_query: 키워드당 최대 광고 수
        country: 국가 코드

    Returns:
        크롤링 결과 딕셔너리
    """
    logger = logging.getLogger('main')
    logger.info("=== Meta 광고 라이브러리 크롤링 시작 ===")

    # 크롤링 설정
    crawl_config = {
        'max_scrolls': 50,
        'scroll_pause': 2,
        'max_retries': 3,
        'page_load_timeout': 10,
    }

    # 프로세서 초기화
    ad_processor = AdProcessor()

    all_results = {}
    all_ads = []

    # 크롤러 시작
    with MetaAdLibraryCrawler(crawl_config) as crawler:
        for query in queries:
            logger.info(f"--- 키워드 '{query}' 크롤링 시작 ---")

            try:
                # 광고 크롤링
                ads = crawler.crawl(query, max_ads=max_ads_per_query, country=country)

                logger.info(f"'{query}' 크롤링 완료: {len(ads)}개 광고")

                # 결과 저장
                all_results[query] = {
                    'query': query,
                    'total_ads': len(ads),
                    'crawl_date': datetime.now().isoformat(),
                    'ads': ads
                }

                all_ads.extend(ads)

                # 개별 쿼리 결과 저장
                query_filename = f"meta_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_results(all_results[query], query_filename)

            except Exception as e:
                logger.error(f"'{query}' 크롤링 중 오류: {e}", exc_info=True)
                continue

    logger.info(f"총 {len(all_ads)}개 광고 수집 완료")

    # 전체 광고 분석
    logger.info("광고 분석 시작...")
    analysis = ad_processor.analyze_ads(all_ads)

    # 종합 결과
    summary = {
        'crawl_date': datetime.now().isoformat(),
        'queries': queries,
        'country': country,
        'total_ads': len(all_ads),
        'results_by_query': all_results,
        'overall_analysis': analysis,
    }

    logger.info("=== Meta 광고 라이브러리 크롤링 완료 ===\n")

    return summary


def crawl_by_category(category_config: Dict) -> Dict:
    """
    카테고리별 Meta 광고 크롤링

    Args:
        category_config: 카테고리 설정

    Returns:
        크롤링 결과
    """
    logger = logging.getLogger('main')

    # 검색 키워드 생성
    queries = []

    # 제품 타입 추가
    product_types = category_config.get('product_types', [])
    queries.extend(product_types[:5])  # 최대 5개

    # 사용자 브랜드 추가
    user_brands = category_config.get('user_brands', [])
    queries.extend(user_brands)

    # 기능 키워드 조합 (선택사항)
    function_keywords = category_config.get('function_keywords', [])
    if function_keywords and product_types:
        for func in function_keywords[:2]:
            for ptype in product_types[:1]:
                queries.append(f"{func} {ptype}")

    # 중복 제거
    queries = list(dict.fromkeys(queries))

    logger.info(f"검색 키워드: {queries}")

    # 크롤링 실행
    max_ads = category_config.get('max_ads_per_query', 100)
    result = crawl_meta_ads(queries, max_ads_per_query=max_ads)

    return result


def main():
    """메인 실행 함수"""
    # 로깅 설정
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("Meta 광고 크롤링 프로그램 시작")

    # 방법 1: 직접 키워드 지정
    queries = [
        "메디큐브",
        "EOA",
        "뷰티디바이스",
        "리프팅",
        "피부관리기기"
    ]

    # 크롤링 실행
    result = crawl_meta_ads(queries, max_ads_per_query=50)

    # 전체 결과 저장
    summary_filename = f"meta_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(result, summary_filename)

    # 통계 출력
    logger.info("\n" + "="*50)
    logger.info("크롤링 요약")
    logger.info("="*50)
    logger.info(f"검색 키워드 수: {len(queries)}")
    logger.info(f"총 수집 광고: {result['total_ads']}개")

    analysis = result.get('overall_analysis', {})
    summary = analysis.get('summary', {})

    logger.info(f"고유 광고주: {summary.get('unique_advertisers', 0)}개")
    logger.info(f"평균 라이브 일수: {summary.get('avg_days_live', 0)}일")

    # 상위 광고주
    advertiser_stats = analysis.get('advertiser_stats', [])
    if advertiser_stats:
        logger.info("\n상위 광고주:")
        for idx, stats in enumerate(advertiser_stats[:5], 1):
            logger.info(f"{idx}. {stats['advertiser']}: {stats['ad_count']}개 광고")

    logger.info("="*50 + "\n")
    logger.info("모든 크롤링 완료!")


def main_with_categories():
    """카테고리 설정 파일을 사용한 크롤링"""
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("Meta 광고 크롤링 프로그램 시작 (카테고리 기반)")

    # 카테고리 설정 로드
    try:
        with open('config/categories.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            categories = config['categories']
    except FileNotFoundError:
        logger.error("config/categories.json 파일을 찾을 수 없습니다")
        return

    # 크롤링할 카테고리 선택
    target_categories = ['뷰티디바이스', '건강기능식품']

    all_results = {}

    for category_name in target_categories:
        if category_name not in categories:
            logger.warning(f"카테고리 '{category_name}'를 찾을 수 없습니다")
            continue

        logger.info(f"\n=== {category_name} 카테고리 크롤링 시작 ===")

        category_config = categories[category_name]
        result = crawl_by_category(category_config)

        all_results[category_name] = result

        # 카테고리별 결과 저장
        filename = f"meta_{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(result, filename)

    # 전체 결과 저장
    summary = {
        'crawl_date': datetime.now().isoformat(),
        'categories': target_categories,
        'results': all_results
    }

    summary_filename = f"meta_all_categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(summary, summary_filename)

    logger.info("\n모든 카테고리 크롤링 완료!")


if __name__ == "__main__":
    # 기본 실행: 직접 키워드 지정
    main()

    # 또는 카테고리 기반 실행
    # main_with_categories()
