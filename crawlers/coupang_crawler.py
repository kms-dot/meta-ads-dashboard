import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class CoupangCrawler(BaseCrawler):
    """쿠팡 크롤러"""

    BASE_URL = "https://www.coupang.com"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "coupang"

    def crawl_products(self, keyword: str) -> List[Dict]:
        """
        쿠팡에서 제품 검색 및 크롤링

        Args:
            keyword: 검색 키워드

        Returns:
            제품 정보 리스트
        """
        self.logger.info(f"쿠팡 크롤링 시작: {keyword}")
        products = []

        try:
            # 검색 페이지로 이동
            search_url = f"{self.BASE_URL}/np/search?q={keyword}"
            self.driver.get(search_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, "#productList", timeout=10)

            # 스크롤하여 더 많은 제품 로드
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 제품 요소 찾기 (여러 선택자 시도)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "#productList li.search-product")

            if not product_elements:
                # 대체 선택자
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.search-product-list li")

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

            self.logger.info(f"쿠팡 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"쿠팡 크롤링 중 오류 발생: {e}")

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
            # 제품명 (여러 선택자 시도)
            name = self.safe_get_text(element, ".name")
            if not name:
                name = self.safe_get_text(element, ".descriptions-inner .descriptions-name")
            if not name:
                name = self.safe_get_text(element, "div.name")

            # 가격
            price_text = self.safe_get_text(element, ".price-value")
            if not price_text:
                price_text = self.safe_get_text(element, "strong.price-value")
            price = self._parse_price(price_text)

            # 브랜드 (쿠팡은 브랜드 정보가 제품명에 포함되어 있음)
            brand = ""

            # 리뷰 수
            review_count_text = self.safe_get_text(element, ".rating-total-count")
            if not review_count_text:
                review_count_text = self.safe_get_text(element, "span.rating-total-count")
            review_count = self._parse_review_count(review_count_text)

            # 평점
            rating_text = self.safe_get_text(element, ".rating")
            if not rating_text:
                rating_text = self.safe_get_attribute(element, ".rating", "data-rating")
            rating = self._parse_rating(rating_text)

            # 상품 링크
            link = self.safe_get_attribute(element, "a.search-product-link", "href")
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            # 이미지 URL
            image_url = self.safe_get_attribute(element, "img.search-product-wrap-img", "src")
            if not image_url:
                image_url = self.safe_get_attribute(element, "dt.image img", "src")

            # 로켓배송 여부
            is_rocket = bool(self.driver.find_elements(By.CSS_SELECTOR, ".badge.rocket"))

            return {
                'name': name,
                'price': price,
                'brand': brand,
                'review_count': review_count,
                'rating': rating,
                'link': link,
                'image_url': image_url,
                'is_rocket': is_rocket
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

    def _parse_review_count(self, review_text: str) -> int:
        """리뷰 수 텍스트를 정수로 변환"""
        try:
            # "(1,234)" -> 1234
            text = review_text.replace('(', '').replace(')', '').replace(',', '').strip()
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

    def crawl_best_products(self, category: str = None) -> List[Dict]:
        """
        쿠팡 베스트 상품 크롤링

        Args:
            category: 카테고리 (선택사항)

        Returns:
            제품 정보 리스트
        """
        self.logger.info("쿠팡 베스트 상품 크롤링 시작")
        products = []

        try:
            # 베스트 페이지로 이동
            best_url = f"{self.BASE_URL}/np/bestsellers"
            self.driver.get(best_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, "ul.baby-product-list", timeout=10)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.baby-product-list li")

            # 각 제품 정보 파싱
            for idx, element in enumerate(product_elements[:self.max_products]):
                try:
                    product_info = self.parse_product_info(element)
                    if product_info and product_info.get('name'):
                        product_info['platform'] = self.platform_name
                        product_info['rank'] = idx + 1
                        product_info['category'] = 'best'
                        products.append(product_info)
                except Exception as e:
                    self.logger.warning(f"제품 파싱 오류: {e}")
                    continue

            self.logger.info(f"베스트 상품 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"베스트 상품 크롤링 중 오류 발생: {e}")

        return products
