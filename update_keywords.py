import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from crawlers import NaverShoppingCrawler, CoupangCrawler, OliveYoungCrawler
from processors import BrandExtractor


# 환경 변수 로드
load_dotenv()


def setup_logging():
    """로깅 설정"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    # 로그 디렉토리 생성
    os.makedirs('output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f'logs/keyword_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )


def load_categories_config() -> Dict:
    """카테고리 설정 로드"""
    try:
        with open('config/categories.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("config/categories.json 파일을 찾을 수 없습니다")
        return {}


def extract_brands_from_ecommerce(
    category_name: str,
    category_config: Dict,
    max_products_per_keyword: int = 100,
    top_brands_count: int = 50
) -> List[str]:
    """
    쇼핑몰에서 브랜드 추출

    Args:
        category_name: 카테고리명
        category_config: 카테고리 설정
        max_products_per_keyword: 키워드당 최대 제품 수
        top_brands_count: 추출할 상위 브랜드 수

    Returns:
        브랜드 리스트
    """
    logger = logging.getLogger('main')
    logger.info(f"=== {category_name} 브랜드 추출 시작 ===")

    # 크롤링 설정
    crawl_config = {
        'crawl_delay_min': 3,
        'crawl_delay_max': 7,
        'max_retry': 3,
        'max_products_per_keyword': max_products_per_keyword,
    }

    # 브랜드 추출기 초기화
    brand_extractor = BrandExtractor(category_config)

    # 검색 키워드 (제품 타입)
    product_types = category_config.get('product_types', [])[:5]  # 상위 5개만

    # 플랫폼
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
                for keyword in product_types:
                    logger.info(f"키워드 '{keyword}' 크롤링 중...")

                    products = crawler.crawl_products(keyword)
                    all_products.extend(products)

                    logger.info(f"'{keyword}' 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            logger.error(f"{platform} 크롤링 중 오류: {e}")
            continue

    logger.info(f"총 {len(all_products)}개 제품 수집 완료")

    # 상위 브랜드 추출
    logger.info("상위 브랜드 추출 중...")
    top_brands = brand_extractor.get_top_brands(
        all_products,
        top_n=top_brands_count,
        sort_by='count'
    )

    # 브랜드명만 추출
    brand_names = [brand for brand, stats in top_brands if brand != 'Unknown']

    # 사용자 지정 브랜드도 포함
    user_brands = category_config.get('user_brands', [])
    brand_names.extend(user_brands)

    # 중복 제거
    brand_names = list(dict.fromkeys(brand_names))

    logger.info(f"브랜드 추출 완료: {len(brand_names)}개")
    logger.info(f"=== {category_name} 브랜드 추출 완료 ===\n")

    return brand_names


def save_extracted_brands(brands_by_category: Dict[str, List[str]]):
    """추출된 브랜드 저장"""
    os.makedirs('output', exist_ok=True)

    filepath = os.path.join('output', 'extracted_brands.json')

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(brands_by_category, f, ensure_ascii=False, indent=2)

    logging.info(f"브랜드 데이터 저장 완료: {filepath}")


def main():
    """메인 실행 함수"""
    # 로깅 설정
    setup_logging()

    logger = logging.getLogger('main')
    logger.info("키워드 자동 업데이트 프로그램 시작")

    # 카테고리 설정 로드
    config = load_categories_config()

    if not config:
        logger.error("카테고리 설정을 불러올 수 없습니다")
        return

    categories = config.get('categories', {})
    settings = config.get('settings', {})

    # 추출 설정
    max_products_per_keyword = settings.get('max_products_per_keyword', 100)
    top_brands_count = settings.get('top_brands_count', 50)

    # 카테고리별 브랜드 추출
    brands_by_category = {}

    # 크롤링할 카테고리 (환경 변수 또는 전체)
    target_categories = os.getenv('TARGET_CATEGORIES', '').split(',')

    if not target_categories or target_categories == ['']:
        # 전체 카테고리
        target_categories = list(categories.keys())

    for category_name in target_categories:
        category_name = category_name.strip()

        if category_name not in categories:
            logger.warning(f"카테고리 '{category_name}'를 찾을 수 없습니다")
            continue

        try:
            category_config = categories[category_name]

            # 브랜드 추출
            brands = extract_brands_from_ecommerce(
                category_name,
                category_config,
                max_products_per_keyword=max_products_per_keyword,
                top_brands_count=top_brands_count
            )

            brands_by_category[category_name] = brands

        except Exception as e:
            logger.error(f"{category_name} 브랜드 추출 중 오류: {e}", exc_info=True)
            continue

    # 결과 저장
    if brands_by_category:
        save_extracted_brands(brands_by_category)

        # 통계 출력
        logger.info("\n" + "="*50)
        logger.info("브랜드 추출 요약")
        logger.info("="*50)

        for category, brands in brands_by_category.items():
            logger.info(f"{category}: {len(brands)}개 브랜드")
            logger.info(f"  상위 10개: {brands[:10]}")

        logger.info("="*50 + "\n")

    logger.info("키워드 업데이트 완료!")


if __name__ == "__main__":
    main()
