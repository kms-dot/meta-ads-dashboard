import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_crawler import BaseCrawler


class NaverShoppingCrawler(BaseCrawler):
    """네이버 쇼핑 크롤러"""

    BASE_URL = "https://shopping.naver.com"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "naver"

    def crawl_products(self, keyword: str) -> List[Dict]:
        """
        네이버 쇼핑에서 제품 검색 및 크롤링

        Args:
            keyword: 검색 키워드

        Returns:
            제품 정보 리스트
        """
        self.logger.info(f"네이버 쇼핑 크롤링 시작: {keyword}")
        products = []

        try:
            # 검색 페이지로 이동
            search_url = f"{self.BASE_URL}/search/all?query={keyword}"
            self.driver.get(search_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, ".basicList_list_basis__uNBZY", timeout=10)

            # 스크롤하여 더 많은 제품 로드
            for _ in range(3):  # 3번 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".basicList_list_basis__uNBZY .product_item__MDtDF")

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

            self.logger.info(f"네이버 쇼핑 크롤링 완료: {len(products)}개 제품")

        except Exception as e:
            self.logger.error(f"네이버 쇼핑 크롤링 중 오류 발생: {e}")

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
            # 제품명
            name = self.safe_get_text(element, ".product_title__Mmw2K")

            # 가격
            price_text = self.safe_get_text(element, ".price_num__S2p_v")
            price = self._parse_price(price_text)

            # 브랜드 (있는 경우)
            brand = self.safe_get_text(element, ".product_mall__M_p6Z")

            # 리뷰 수
            review_count_text = self.safe_get_text(element, ".product_num__fxk7O")
            review_count = self._parse_review_count(review_count_text)

            # 평점
            rating_text = self.safe_get_text(element, ".product_grade__IzyU3")
            rating = self._parse_rating(rating_text)

            # 상품 링크
            link = self.safe_get_attribute(element, ".product_link__TrAac", "href")

            # 이미지 URL
            image_url = self.safe_get_attribute(element, ".product_img__PDV1f img", "src")

            return {
                'name': name,
                'price': price,
                'brand': brand,
                'review_count': review_count,
                'rating': rating,
                'link': link,
                'image_url': image_url
            }

        except Exception as e:
            self.logger.debug(f"제품 정보 파싱 오류: {e}")
            return {}

    def _parse_price(self, price_text: str) -> int:
        """가격 텍스트를 정수로 변환"""
        try:
            # "1,234원" -> 1234
            return int(price_text.replace(',', '').replace('원', '').strip())
        except (ValueError, AttributeError):
            return 0

    def _parse_review_count(self, review_text: str) -> int:
        """리뷰 수 텍스트를 정수로 변환"""
        try:
            # "리뷰 1,234" -> 1234
            text = review_text.replace('리뷰', '').replace(',', '').strip()
            return int(text) if text else 0
        except (ValueError, AttributeError):
            return 0

    def _parse_rating(self, rating_text: str) -> float:
        """평점 텍스트를 실수로 변환"""
        try:
            # "별점 4.5" -> 4.5
            text = rating_text.replace('별점', '').strip()
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
        self.logger.info(f"네이버 쇼핑 카테고리 크롤링 시작: {category_url}")
        products = []

        try:
            self.driver.get(category_url)
            self.random_delay()

            # 페이지 로드 대기
            self.wait_for_element(By.CSS_SELECTOR, ".basicList_list_basis__uNBZY", timeout=10)

            # 스크롤하여 더 많은 제품 로드
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # 제품 요소 찾기
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".basicList_list_basis__uNBZY .product_item__MDtDF")

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
