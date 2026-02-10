import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from crawlers import NaverShoppingCrawler, CoupangCrawler, OliveYoungCrawler
from processors import KeywordCleaner, BrandExtractor


# 환경 변수 로드
load_dotenv()


def setup_logging():
    """로깅 설정"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'output/crawl_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )


def load_config() -> Dict:
    """카테고리 설정 로드"""
    with open('config/categories.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def save_results(data: Dict, filename: str):
    """결과 저장"""
    os.makedirs('output', exist_ok=True)

    filepath = os.path.join('output', filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"결과 저장 완료: {filepath}")


def crawl_category(category_name: str, category_config: Dict, settings: Dict) -> Dict:
    """
    카테고리별 크롤링 실행

    Args:
        category_name: 카테고리명
        category_config: 카테고리 설정
        settings: 전역 설정

    Returns:
        크롤링 결과 딕셔너리
    """
    logger = logging.getLogger('main')
    logger.info(f"=== {category_name} 크롤링 시작 ===")

    # 크롤링 설정
    crawl_config = {
        'crawl_delay_min': settings.get('crawl_delay_min', 3),
        'crawl_delay_max': settings.get('crawl_delay_max', 7),
        'max_retry': settings.get('max_retry', 3),
        'max_products_per_keyword': settings.get('max_products_per_keyword', 100),
    }

    # 프로세서 초기화
    keyword_cleaner = KeywordCleaner(category_config)
    brand_extractor = BrandExtractor(category_config)

    # 검색 키워드 생성
    search_keywords = keyword_cleaner.generate_search_keywords(
        category_config,
        max_keywords=settings.get('search_keywords_limit', 5)
    )

    # 사용자 지정 브랜드 추가
    user_brands = category_config.get('user_brands', [])
    search_keywords.extend(user_brands)

    logger.info(f"검색 키워드: {search_keywords}")

    # 크롤링 플랫폼
    platforms = category_config.get('crawl_platforms', ['naver', 'coupang'])

    all_products = []

    # 각 플랫폼별 크롤링
    for platform in platforms:
        logger.info(f"--- {platform} 크롤링 시작 ---")

        try:
            # 크롤러 선택
            if platform == 'naver':
                crawler_class = NaverShoppingCrawler
            elif platform == 'coupang':
                crawler_class = CoupangCrawler
            elif platform == 'oliveyoung':
                crawler_class = OliveYoungCrawler
            else:
                logger.warning(f"알 수 없는 플랫폼: {platform}")
                continue

            # 크롤러 실행
            with crawler_class(crawl_config) as crawler:
                # 각 키워드별 크롤링
                for keyword in search_keywords:
                    logger.info(f"키워드 '{keyword}' 크롤링 중...")

                    products = crawler.crawl_products(keyword)
                    all_products.extend(products)

                    logger.info(f"'{keyword}' 크롤링 완료: {len(products)}개 제품")

                # 올리브영 카테고리 URL이 있으면 추가 크롤링
                if platform == 'oliveyoung' and category_config.get('oliveyoung_url'):
                    logger.info("올리브영 카테고리 페이지 크롤링 중...")
                    category_products = crawler.crawl_category_products(
                        category_config['oliveyoung_url']
                    )
                    all_products.extend(category_products)

        except Exception as e:
            logger.error(f"{platform} 크롤링 중 오류: {e}")
            continue

    logger.info(f"총 {len(all_products)}개 제품 크롤링 완료")

    # 브랜드 분석
    logger.info("브랜드 분석 시작...")
    brand_report = brand_extractor.create_brand_report(
        all_products,
        top_n=settings.get('top_brands_count', 50)
    )

    # 키워드 분석
    logger.info("키워드 분석 시작...")
    top_keywords = keyword_cleaner.get_top_keywords(
        all_products,
        top_n=settings.get('top_brands_count', 50)
    )

    # 결과 정리
    result = {
        'category': category_name,
        'crawl_date': datetime.now().isoformat(),
        'search_keywords': search_keywords,
        'platforms': platforms,
        'total_products': len(all_products),
        'products': all_products,
        'brand_analysis': brand_report,
        'top_keywords': [
            {'keyword': keyword, 'count': count}
            for keyword, count in top_keywords
        ]
    }

    logger.info(f"=== {category_name} 크롤링 완료 ===\n")

    return result


def main():
    """메인 실행 함수"""
    # 로깅 설정
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("크롤링 프로그램 시작")

    # 설정 로드
    config = load_config()
    categories = config['categories']
    settings = config['settings']

    # 전체 결과 저장
    all_results = {}

    # 각 카테고리별 크롤링
    for category_name, category_config in categories.items():
        try:
            result = crawl_category(category_name, category_config, settings)
            all_results[category_name] = result

            # 카테고리별 결과 저장
            filename = f"{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_results(result, filename)

        except Exception as e:
            logger.error(f"{category_name} 크롤링 중 오류: {e}", exc_info=True)
            continue

    # 전체 결과 저장
    summary_filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(all_results, summary_filename)

    logger.info("모든 크롤링 완료!")


if __name__ == "__main__":
    main()
