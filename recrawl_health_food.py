"""
건강기능식품 카테고리만 재크롤링하는 스크립트
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from meta_crawlers import MetaAdLibraryCrawler
from meta_processors import AdProcessor
from main_meta import crawl_by_category, save_results

# 환경 변수 로드
load_dotenv()


def setup_logging():
    """로깅 설정"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    os.makedirs('meta_output', exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f'meta_output/meta_crawl_health_food_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )


def main():
    """건강기능식품 재크롤링"""
    setup_logging()
    logger = logging.getLogger('main')

    logger.info("="*60)
    logger.info("건강기능식품 카테고리 재크롤링 시작")
    logger.info("="*60)

    # 카테고리 설정 로드
    try:
        with open('config/categories.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            categories = config['categories']
    except FileNotFoundError:
        logger.error("config/categories.json 파일을 찾을 수 없습니다")
        return

    # 건강기능식품만 크롤링
    category_name = '건강기능식품'

    if category_name not in categories:
        logger.error(f"'{category_name}' 카테고리를 찾을 수 없습니다")
        return

    logger.info(f"\n=== {category_name} 카테고리 크롤링 시작 (목표: 200개 이상) ===")

    category_config = categories[category_name]

    # 크롤링 실행
    result = crawl_by_category(category_config, min_ads_per_category=200)

    # 결과 저장
    filename = f"meta_{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(result, filename)

    # 통계 출력
    logger.info("\n" + "="*60)
    logger.info(f"{category_name} 크롤링 완료")
    logger.info("="*60)
    logger.info(f"총 광고 수: {result['total_ads']}개")

    analysis = result.get('overall_analysis', {})
    summary = analysis.get('summary', {})

    logger.info(f"고유 광고주: {summary.get('unique_advertisers', 0)}개")
    logger.info(f"평균 라이브 일수: {summary.get('avg_days_live', 0):.1f}일")

    # 상위 광고주
    advertiser_stats = analysis.get('advertiser_stats', [])
    if advertiser_stats:
        logger.info("\n상위 광고주 TOP 5:")
        for idx, stats in enumerate(advertiser_stats[:5], 1):
            logger.info(f"{idx}. {stats['advertiser']}: {stats['ad_count']}개")

    # 목표 달성 여부
    target = 200
    if result['total_ads'] >= target:
        logger.info(f"\n✅ 목표 달성! {result['total_ads']}/{target}개")
    else:
        logger.warning(f"\n⚠️ 목표 미달: {result['total_ads']}/{target}개 (부족: {target - result['total_ads']}개)")

    logger.info("="*60)


if __name__ == "__main__":
    main()
