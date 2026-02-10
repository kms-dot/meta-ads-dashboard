import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from meta_crawlers import MetaAdLibraryCrawler
from meta_processors import AdProcessor
from database import AdRepository, KeywordRepository, CrawlLogRepository


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
                f'meta_output/meta_crawl_db_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )


def save_results_to_file(data: Dict, filename: str):
    """결과를 JSON 파일로도 저장 (백업용)"""
    os.makedirs('meta_output', exist_ok=True)

    filepath = os.path.join('meta_output', filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"파일 저장 완료: {filepath}")


def crawl_and_save_to_db(
    queries: List[str],
    category: str,
    max_ads_per_query: int = 100,
    country: str = 'KR'
) -> Dict:
    """
    Meta 광고 크롤링 및 DB 저장

    Args:
        queries: 검색 키워드 리스트
        category: 카테고리명
        max_ads_per_query: 키워드당 최대 광고 수
        country: 국가 코드

    Returns:
        크롤링 결과
    """
    logger = logging.getLogger('main')
    logger.info(f"=== Meta 광고 크롤링 & DB 저장 시작: {category} ===")

    # Repository 초기화
    ad_repo = AdRepository()
    keyword_repo = KeywordRepository()
    crawl_log_repo = CrawlLogRepository()

    # 크롤링 설정
    crawl_config = {
        'max_scrolls': 50,
        'scroll_pause': 2,
        'max_retries': 3,
        'page_load_timeout': 10,
    }

    # 프로세서 초기화
    ad_processor = AdProcessor()

    all_ads = []
    all_results = {}

    # 크롤링 로그 시작
    log_id = crawl_log_repo.start_crawl_log(
        crawl_type='meta_ads',
        category=category,
        platform='meta'
    )

    try:
        # 크롤러 시작
        with MetaAdLibraryCrawler(crawl_config) as crawler:
            for query in queries:
                logger.info(f"--- 키워드 '{query}' 크롤링 시작 ---")

                # 키워드별 로그
                query_log_id = crawl_log_repo.start_crawl_log(
                    crawl_type='meta_ads',
                    category=category,
                    platform='meta',
                    query=query
                )

                try:
                    # 광고 크롤링
                    ads = crawler.crawl(query, max_ads=max_ads_per_query, country=country)

                    logger.info(f"'{query}' 크롤링 완료: {len(ads)}개 광고")

                    # DB에 저장
                    if ads:
                        save_stats = ad_repo.save_ads_batch(ads, category)
                        logger.info(
                            f"DB 저장 완료: 총 {save_stats['total']}개, "
                            f"성공 {save_stats['inserted']}개, 실패 {save_stats['failed']}개"
                        )

                        # 키워드 검색 통계 업데이트 (키워드 ID가 있다면)
                        # keyword_repo.update_search_stats(keyword_id, ads_found=len(ads))

                    # 쿼리별 로그 완료
                    crawl_log_repo.complete_crawl_log(
                        log_id=query_log_id,
                        items_collected=len(ads),
                        items_new=save_stats.get('inserted', 0) if ads else 0,
                        status='success'
                    )

                    # 결과 저장
                    all_results[query] = {
                        'query': query,
                        'total_ads': len(ads),
                        'crawl_date': datetime.now().isoformat(),
                    }

                    all_ads.extend(ads)

                except Exception as e:
                    logger.error(f"'{query}' 크롤링 중 오류: {e}", exc_info=True)

                    # 실패 로그
                    crawl_log_repo.fail_crawl_log(query_log_id, str(e))
                    continue

        logger.info(f"총 {len(all_ads)}개 광고 수집 완료")

        # 전체 광고 분석
        logger.info("광고 분석 시작...")
        analysis = ad_processor.analyze_ads(all_ads)

        # 크롤링 로그 완료
        crawl_log_repo.complete_crawl_log(
            log_id=log_id,
            items_collected=len(all_ads),
            items_new=len(all_ads),  # 실제로는 save_stats 집계 필요
            status='success'
        )

        # 종합 결과
        summary = {
            'category': category,
            'crawl_date': datetime.now().isoformat(),
            'queries': queries,
            'country': country,
            'total_ads': len(all_ads),
            'results_by_query': all_results,
            'overall_analysis': analysis,
        }

        # 파일로도 저장 (백업)
        filename = f"meta_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results_to_file(summary, filename)

        logger.info(f"=== {category} 크롤링 완료 ===\n")

        return summary

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}", exc_info=True)

        # 실패 로그
        crawl_log_repo.fail_crawl_log(log_id, str(e))

        return {
            'category': category,
            'error': str(e),
            'total_ads': 0
        }


def load_keywords_from_db(category: str) -> List[str]:
    """
    DB에서 키워드 로드

    Args:
        category: 카테고리명

    Returns:
        키워드 리스트
    """
    logger = logging.getLogger('main')

    keyword_repo = KeywordRepository()
    keywords_dict = keyword_repo.get_keywords_by_category(category)

    # 브랜드 키워드와 제품 타입 키워드 합치기
    all_keywords = []
    all_keywords.extend(keywords_dict.get('brands', []))
    all_keywords.extend(keywords_dict.get('product_types', []))

    logger.info(f"DB에서 {len(all_keywords)}개 키워드 로드: {category}")

    return all_keywords


def setup_keywords_in_db():
    """
    카테고리 설정 파일의 키워드를 DB에 저장
    (최초 1회 실행)
    """
    logger = logging.getLogger('main')
    logger.info("=== 키워드 DB 초기 설정 시작 ===")

    # 카테고리 설정 로드
    try:
        with open('config/categories.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            categories = config['categories']
    except FileNotFoundError:
        logger.error("config/categories.json 파일을 찾을 수 없습니다")
        return

    keyword_repo = KeywordRepository()

    for category_name, category_config in categories.items():
        logger.info(f"--- {category_name} 키워드 저장 중 ---")

        keywords_dict = {
            'product_types': category_config.get('product_types', []),
            'brands': category_config.get('user_brands', []),
            'functions': category_config.get('function_keywords', [])
        }

        stats = keyword_repo.save_keywords_batch(
            category=category_name,
            keywords_dict=keywords_dict,
            source='user_provided'
        )

        logger.info(f"{category_name}: {stats['inserted']}개 키워드 저장 완료")

    logger.info("=== 키워드 DB 초기 설정 완료 ===\n")


def main():
    """메인 실행 함수"""
    # 로깅 설정
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("Meta 광고 크롤링 프로그램 시작 (DB 연동)")

    # 방법 1: 직접 키워드 지정
    category = "뷰티디바이스"
    queries = [
        "메디큐브",
        "EOA",
        "뷰티디바이스",
        "리프팅"
    ]

    # 크롤링 및 DB 저장
    result = crawl_and_save_to_db(queries, category, max_ads_per_query=50)

    # 통계 출력
    logger.info("\n" + "="*50)
    logger.info("크롤링 요약")
    logger.info("="*50)
    logger.info(f"카테고리: {result.get('category')}")
    logger.info(f"총 수집 광고: {result.get('total_ads', 0)}개")

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


def main_with_db_keywords():
    """DB에 저장된 키워드로 크롤링"""
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("Meta 광고 크롤링 프로그램 시작 (DB 키워드 사용)")

    # 크롤링할 카테고리
    categories = ['뷰티디바이스', '건강기능식품']

    for category in categories:
        # DB에서 키워드 로드
        queries = load_keywords_from_db(category)

        if not queries:
            logger.warning(f"{category} 카테고리의 키워드가 없습니다")
            continue

        # 크롤링 및 DB 저장
        result = crawl_and_save_to_db(queries, category, max_ads_per_query=50)

        logger.info(f"{category}: {result.get('total_ads', 0)}개 광고 수집")

    logger.info("\n모든 카테고리 크롤링 완료!")


if __name__ == "__main__":
    # 최초 1회 실행: 키워드 DB 설정
    # setup_keywords_in_db()

    # 기본 실행: 직접 키워드 지정
    main()

    # 또는 DB 키워드 사용
    # main_with_db_keywords()
