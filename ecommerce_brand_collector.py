"""
이커머스 플랫폼 브랜드 자동 수집기

네이버쇼핑, 쿠팡, 올리브영에서 베스트셀러 상품의 브랜드명을 자동 수집합니다.
"""

import json
import re
import time
from typing import List, Dict, Set
from collections import Counter
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote


class EcommerceBrandCollector:
    """이커머스 플랫폼에서 브랜드를 수집하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger('BrandCollector')
        self.driver = None

        # 브랜드명 정제 규칙
        self.noise_keywords = [
            '추천', '후기', '가격', '순위', '베스트', 'BEST', '인기',
            '할인', '특가', '세트', '기획', '증정', '사은품',
            '공식', '정품', '리뷰', '평점', '배송', '무료'
        ]

    def start_driver(self):
        """Chrome 드라이버 시작"""
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.logger.info("Chrome 드라이버 시작 완료")

    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Chrome 드라이버 종료")

    def clean_brand_name(self, text: str) -> str:
        """브랜드명 정제"""
        if not text:
            return ""

        # 1. 노이즈 키워드 제거
        for noise in self.noise_keywords:
            text = re.sub(rf'\b{re.escape(noise)}\b', '', text, flags=re.IGNORECASE)

        # 2. 특수문자 제거 (단, 한글/영문/숫자/공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 3. 연속 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()

        # 4. 숫자만 있는 경우 제외
        if text.isdigit():
            return ""

        # 5. 너무 짧은 브랜드명 제외 (1글자)
        if len(text) <= 1:
            return ""

        return text

    def collect_from_naver(self, keyword: str, max_items: int = 100) -> List[str]:
        """네이버쇼핑에서 브랜드 수집"""
        self.logger.info(f"네이버쇼핑 수집 시작: {keyword}")

        try:
            url = f"https://search.shopping.naver.com/search/all?query={quote(keyword)}&cat_id=&frm=NVSHATC"
            self.driver.get(url)
            time.sleep(3)

            brands = []

            # 상품 카드 찾기
            product_selectors = [
                "div.product_item__MDtDF",
                "div.product_info_area__xxCTi",
                "li.basicList_item__2XT81"
            ]

            products = []
            for selector in product_selectors:
                try:
                    products = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if products:
                        break
                except:
                    continue

            if not products:
                self.logger.warning(f"네이버쇼핑 상품을 찾을 수 없음: {keyword}")
                return []

            for idx, product in enumerate(products[:max_items]):
                if idx >= max_items:
                    break

                try:
                    # 브랜드명 찾기 (여러 셀렉터 시도)
                    brand_selectors = [
                        "span.product_mall__LYHRo",
                        "span.product_item__brand",
                        "div.product_title__Mmw2K",
                        "a.product_link__TrAac"
                    ]

                    for selector in brand_selectors:
                        try:
                            brand_elem = product.find_element(By.CSS_SELECTOR, selector)
                            brand_text = brand_elem.text.strip()
                            if brand_text:
                                # 상품명에서 브랜드 추출 (첫 단어)
                                brand_parts = brand_text.split()
                                if brand_parts:
                                    brand = self.clean_brand_name(brand_parts[0])
                                    if brand:
                                        brands.append(brand)
                                        break
                        except:
                            continue
                except Exception as e:
                    self.logger.debug(f"상품 {idx} 처리 오류: {e}")
                    continue

            self.logger.info(f"네이버쇼핑 수집 완료: {len(brands)}개 브랜드")
            return brands

        except Exception as e:
            self.logger.error(f"네이버쇼핑 수집 오류: {e}")
            return []

    def collect_from_coupang(self, keyword: str, max_items: int = 100) -> List[str]:
        """쿠팡에서 브랜드 수집 (로켓배송 베스트)"""
        self.logger.info(f"쿠팡 수집 시작: {keyword}")

        try:
            url = f"https://www.coupang.com/np/search?q={quote(keyword)}&channel=user"
            self.driver.get(url)
            time.sleep(3)

            brands = []

            # 상품 리스트 찾기
            product_selectors = [
                "li.search-product",
                "div.search-product"
            ]

            products = []
            for selector in product_selectors:
                try:
                    products = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if products:
                        break
                except:
                    continue

            if not products:
                self.logger.warning(f"쿠팡 상품을 찾을 수 없음: {keyword}")
                return []

            for idx, product in enumerate(products[:max_items]):
                if idx >= max_items:
                    break

                try:
                    # 상품명에서 브랜드 추출
                    name_elem = product.find_element(By.CSS_SELECTOR, "div.name")
                    product_name = name_elem.text.strip()

                    if product_name:
                        # 대괄호 안의 브랜드명 추출 [브랜드]
                        bracket_match = re.search(r'\[([^\]]+)\]', product_name)
                        if bracket_match:
                            brand = self.clean_brand_name(bracket_match.group(1))
                            if brand:
                                brands.append(brand)
                        else:
                            # 첫 단어를 브랜드로 간주
                            first_word = product_name.split()[0] if product_name.split() else ""
                            brand = self.clean_brand_name(first_word)
                            if brand:
                                brands.append(brand)
                except:
                    continue

            self.logger.info(f"쿠팡 수집 완료: {len(brands)}개 브랜드")
            return brands

        except Exception as e:
            self.logger.error(f"쿠팡 수집 오류: {e}")
            return []

    def collect_from_oliveyoung(self, category_url: str, max_items: int = 100) -> List[str]:
        """올리브영에서 브랜드 수집"""
        self.logger.info(f"올리브영 수집 시작: {category_url}")

        try:
            self.driver.get(category_url)
            time.sleep(3)

            brands = []

            # 상품 리스트 찾기
            product_selectors = [
                "div.prd_info",
                "li.item"
            ]

            products = []
            for selector in product_selectors:
                try:
                    products = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if products:
                        break
                except:
                    continue

            if not products:
                self.logger.warning("올리브영 상품을 찾을 수 없음")
                return []

            for idx, product in enumerate(products[:max_items]):
                if idx >= max_items:
                    break

                try:
                    # 브랜드명 찾기
                    brand_selectors = [
                        "span.tx_brand",
                        "p.tx_brand"
                    ]

                    for selector in brand_selectors:
                        try:
                            brand_elem = product.find_element(By.CSS_SELECTOR, selector)
                            brand_text = brand_elem.text.strip()
                            if brand_text:
                                brand = self.clean_brand_name(brand_text)
                                if brand:
                                    brands.append(brand)
                                    break
                        except:
                            continue
                except:
                    continue

            self.logger.info(f"올리브영 수집 완료: {len(brands)}개 브랜드")
            return brands

        except Exception as e:
            self.logger.error(f"올리브영 수집 오류: {e}")
            return []

    def collect_brands_for_category(self, category_name: str, category_config: Dict) -> List[str]:
        """카테고리별 브랜드 수집"""
        self.logger.info(f"\n=== {category_name} 카테고리 브랜드 수집 시작 ===")

        all_brands = []

        # 1. 제품 타입 키워드로 네이버쇼핑 수집
        product_types = category_config.get('product_types', [])
        for product_type in product_types[:3]:  # 상위 3개만
            brands = self.collect_from_naver(product_type, max_items=50)
            all_brands.extend(brands)
            time.sleep(2)

        # 2. 쿠팡 수집
        if 'coupang' in category_config.get('crawl_platforms', []):
            for product_type in product_types[:2]:  # 상위 2개만
                brands = self.collect_from_coupang(product_type, max_items=50)
                all_brands.extend(brands)
                time.sleep(2)

        # 3. 올리브영 수집 (뷰티 카테고리만)
        oliveyoung_url = category_config.get('oliveyoung_url')
        if oliveyoung_url:
            brands = self.collect_from_oliveyoung(oliveyoung_url, max_items=100)
            all_brands.extend(brands)

        # 브랜드 빈도 분석 및 상위 추출
        brand_counter = Counter(all_brands)
        top_brands = [brand for brand, count in brand_counter.most_common(20) if count >= 2]

        self.logger.info(f"{category_name} 수집 완료: {len(top_brands)}개 고유 브랜드")

        return top_brands


def update_categories_with_auto_brands(config_path: str = 'config/categories.json'):
    """카테고리 설정에 자동 수집 브랜드 추가"""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger('BrandCollector')

    # 기존 설정 로드
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    collector = EcommerceBrandCollector()

    try:
        collector.start_driver()

        for category_name, category_config in config['categories'].items():
            logger.info(f"\n{'='*60}")
            logger.info(f"카테고리: {category_name}")
            logger.info(f"{'='*60}")

            # 기존 브랜드
            existing_brands = set(category_config.get('user_brands', []))
            logger.info(f"기존 브랜드: {len(existing_brands)}개")

            # 자동 수집
            auto_brands = collector.collect_brands_for_category(category_name, category_config)

            # 병합 (중복 제거)
            all_brands = list(existing_brands.union(set(auto_brands)))
            all_brands.sort()

            # 업데이트
            config['categories'][category_name]['user_brands'] = all_brands

            logger.info(f"최종 브랜드: {len(all_brands)}개 (기존 {len(existing_brands)} + 신규 {len(auto_brands) - len(existing_brands.intersection(auto_brands))})")

        # 백업
        backup_path = config_path.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"\n백업 완료: {backup_path}")

        # 저장
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"설정 업데이트 완료: {config_path}")

    finally:
        collector.close_driver()

    logger.info("\n모든 카테고리 브랜드 수집 완료!")


if __name__ == "__main__":
    update_categories_with_auto_brands()
