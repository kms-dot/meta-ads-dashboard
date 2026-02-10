import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class OliveYoungCrawler(BaseCrawler):
    """올리브영 크롤러"""

    BASE_URL = "https://www.oliveyoung.co.kr"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "oliveyoung"

    def crawl_products(self, keyword: str) -> List[Dict]:
        """
        올리브영에서 제품 검색 및 크롤링

        Args:
            keyword: 검색 키워드

        Returns:
            제품 정보 리스트
        """
        self.logger.info(f"올리브영 크롤링 시작: {keyword}")
        products = []

        try:
            # 검색 페이지로 이동
            search_url = f"{self.BASE_URL}/store/search/getSearchMain.do?query={keyword}"
            self.driver.get(search_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, ".prd_list_type01", timeout=10)

            # 스크롤하여 더 많은 제품 로드
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".prd_list_type01 li")

            if not product_elements:
                # 대체 선택자
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.cate_prd_list li")

            self.logger.info(f"발견된 제품 수: {len(product_elements)}")

            # 각 제품 정보 파싱
            for idx, element in enumerate(product_elements[:self.max_products]):
                try:
                    product_info = self.parse_product_info(element)
                    if product_info and product_info.get('name'):
                        product_info['keyword'] = keyword
                        product_info['platform'] = self.platform_name
                        product_info['rank'] = idx + 1
                        products.append(product_info)
                except Exception as e:
                    self.logger.warning(f"제품 파싱 오류 (인덱스 {idx}): {e}")
                    continue

            self.logger.info(f"올리브영 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"올리브영 크롤링 중 오류 발생: {e}")

        return products

    def parse_product_info(self, element) -> Dict:
        """
        제품 요소에서 정보 추출

        Args:
            element: 제품 요소

        Returns:
            제품 정보 딕셔너리
        """
        try:
            # 브랜드
            brand = self.safe_get_text(element, ".tx_brand")

            # 제품명
            name = self.safe_get_text(element, ".tx_name")

            # 가격 (할인가 우선, 없으면 정가)
            price_text = self.safe_get_text(element, ".price-2")
            if not price_text:
                price_text = self.safe_get_text(element, ".price")
            price = self._parse_price(price_text)

            # 원가 (할인 전 가격)
            original_price_text = self.safe_get_text(element, ".price-1")
            original_price = self._parse_price(original_price_text) if original_price_text else price

            # 할인율
            discount_text = self.safe_get_text(element, ".per")
            discount_rate = self._parse_discount(discount_text)

            # 리뷰 수
            review_count_text = self.safe_get_text(element, ".reviewCount")
            review_count = self._parse_review_count(review_count_text)

            # 평점
            rating_text = self.safe_get_attribute(element, ".review", "data-score")
            if not rating_text:
                rating_text = self.safe_get_text(element, ".point")
            rating = self._parse_rating(rating_text)

            # 상품 링크
            link = self.safe_get_attribute(element, "a.prd_thumb", "href")
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            # 이미지 URL
            image_url = self.safe_get_attribute(element, "img", "src")
            if not image_url:
                image_url = self.safe_get_attribute(element, "img", "data-src")

            # 세일 여부
            is_sale = bool(self.safe_get_text(element, ".ico_flag_sale"))

            # 베스트 여부
            is_best = bool(self.safe_get_text(element, ".ico_flag_best"))

            return {
                'name': name,
                'brand': brand,
                'price': price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'review_count': review_count,
                'rating': rating,
                'link': link,
                'image_url': image_url,
                'is_sale': is_sale,
                'is_best': is_best
            }

        except Exception as e:
            self.logger.debug(f"제품 정보 파싱 오류: {e}")
            return {}

    def _parse_price(self, price_text: str) -> int:
        """가격 텍스트를 정수로 변환"""
        try:
            # "12,340원" -> 12340
            text = price_text.replace(',', '').replace('원', '').strip()
            return int(text) if text else 0
        except (ValueError, AttributeError):
            return 0

    def _parse_discount(self, discount_text: str) -> int:
        """할인율 텍스트를 정수로 변환"""
        try:
            # "30%" -> 30
            text = discount_text.replace('%', '').strip()
            return int(text) if text else 0
        except (ValueError, AttributeError):
            return 0

    def _parse_review_count(self, review_text: str) -> int:
        """리뷰 수 텍스트를 정수로 변환"""
        try:
            # "1,234" -> 1234
            text = review_text.replace(',', '').strip()
            return int(text) if text else 0
        except (ValueError, AttributeError):
            return 0

    def _parse_rating(self, rating_text: str) -> float:
        """평점 텍스트를 실수로 변환"""
        try:
            # "4.5" -> 4.5
            text = rating_text.strip()
            return float(text) if text else 0.0
        except (ValueError, AttributeError):
            return 0.0

    def crawl_category_products(self, category_url: str) -> List[Dict]:
        """
        카테고리 페이지에서 제품 크롤링

        Args:
            category_url: 카테고리 URL

        Returns:
            제품 정보 리스트
        """
        self.logger.info(f"올리브영 카테고리 크롤링 시작: {category_url}")
        products = []

        try:
            self.driver.get(category_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, ".cate_prd_list", timeout=10)

            # 스크롤하여 더 많은 제품 로드
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.cate_prd_list > li")

            # 각 제품 정보 파싱
            for idx, element in enumerate(product_elements[:self.max_products]):
                try:
                    product_info = self.parse_product_info(element)
                    if product_info and product_info.get('name'):
                        product_info['platform'] = self.platform_name
                        product_info['rank'] = idx + 1
                        products.append(product_info)
                except Exception as e:
                    self.logger.warning(f"제품 파싱 오류: {e}")
                    continue

            self.logger.info(f"카테고리 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"카테고리 크롤링 중 오류 발생: {e}")

        return products

    def crawl_ranking_products(self, category: str = "total") -> List[Dict]:
        """
        올리브영 랭킹 상품 크롤링

        Args:
            category: 카테고리 (total, skincare, makeup 등)

        Returns:
            제품 정보 리스트
        """
        self.logger.info(f"올리브영 랭킹 크롤링 시작: {category}")
        products = []

        try:
            # 랭킹 페이지로 이동
            ranking_url = f"{self.BASE_URL}/store/main/getBestList.do"
            self.driver.get(ranking_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, ".rank_list", timeout=10)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".rank_list li")

            # 각 제품 정보 파싱
            for idx, element in enumerate(product_elements[:self.max_products]):
                try:
                    product_info = self.parse_product_info(element)
                    if product_info and product_info.get('name'):
                        product_info['platform'] = self.platform_name
                        product_info['rank'] = idx + 1
                        product_info['category'] = category
                        products.append(product_info)
                except Exception as e:
                    self.logger.warning(f"제품 파싱 오류: {e}")
                    continue

            self.logger.info(f"랭킹 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"랭킹 크롤링 중 오류 발생: {e}")

        return products
