import logging
from typing import List, Dict, Set
from collections import Counter
import re


class BrandExtractor:
    """제품 정보에서 브랜드를 추출하고 분석하는 클래스"""

    def __init__(self, config: Dict):
        """
        초기화

        Args:
            config: 카테고리 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 사용자 지정 브랜드
        self.user_brands = set(config.get('user_brands', []))

        # 브랜드명 정규화 맵
        self.brand_aliases = self._load_brand_aliases()

    def _load_brand_aliases(self) -> Dict[str, str]:
        """
        브랜드 별칭 매핑 로드
        (같은 브랜드의 다양한 표기를 통일)

        Returns:
            {별칭: 정식명칭} 딕셔너리
        """
        aliases = {
            # 예시
            'medicube': '메디큐브',
            'medcube': '메디큐브',
            '메디큐브ar': '메디큐브에이지알',
            '메디큐브booster': '메디큐브부스터프로',
            'eoa': 'EOA',
            'fullcera': '풀쎄라',
            'fulltenza': '풀텐자',
            'quadcera': '쿼드쎄라',
        }
        return aliases

    def extract_brand_from_name(self, product_name: str) -> str:
        """
        제품명에서 브랜드 추출

        Args:
            product_name: 제품명

        Returns:
            브랜드명 (없으면 빈 문자열)
        """
        if not product_name:
            return ""

        # 제품명을 소문자로 변환
        name_lower = product_name.lower()

        # 사용자 지정 브랜드 먼저 체크
        for brand in self.user_brands:
            if brand.lower() in name_lower:
                return brand

        # 브랜드 별칭 체크
        for alias, official_name in self.brand_aliases.items():
            if alias.lower() in name_lower:
                return official_name

        # 일반적인 브랜드 패턴 추출 (대괄호 안의 텍스트)
        bracket_pattern = r'\[([^\]]+)\]'
        matches = re.findall(bracket_pattern, product_name)
        if matches:
            return matches[0].strip()

        return ""

    def extract_brand(self, product: Dict) -> str:
        """
        제품 정보에서 브랜드 추출

        Args:
            product: 제품 정보 딕셔너리

        Returns:
            브랜드명
        """
        # 1. 명시적 브랜드 필드가 있으면 사용
        if product.get('brand'):
            brand = product['brand']
            # 별칭 정규화
            normalized = self.normalize_brand(brand)
            return normalized

        # 2. 제품명에서 추출
        product_name = product.get('name', '')
        return self.extract_brand_from_name(product_name)

    def normalize_brand(self, brand_name: str) -> str:
        """
        브랜드명 정규화

        Args:
            brand_name: 원본 브랜드명

        Returns:
            정규화된 브랜드명
        """
        if not brand_name:
            return ""

        # 소문자 변환
        normalized = brand_name.lower().strip()

        # 별칭 체크
        if normalized in self.brand_aliases:
            return self.brand_aliases[normalized]

        # 특수문자 제거
        normalized = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', '', normalized)

        # 공백 제거
        normalized = normalized.replace(' ', '')

        return normalized

    def get_brand_statistics(self, products: List[Dict]) -> Dict[str, Dict]:
        """
        브랜드별 통계 계산

        Args:
            products: 제품 정보 리스트

        Returns:
            브랜드별 통계 딕셔너리
        """
        brand_stats = {}

        for product in products:
            # 브랜드 추출
            brand = self.extract_brand(product)
            if not brand:
                brand = "Unknown"

            # 통계 초기화
            if brand not in brand_stats:
                brand_stats[brand] = {
                    'count': 0,
                    'total_reviews': 0,
                    'total_rating': 0.0,
                    'avg_price': 0,
                    'products': []
                }

            # 통계 업데이트
            brand_stats[brand]['count'] += 1
            brand_stats[brand]['total_reviews'] += product.get('review_count', 0)
            brand_stats[brand]['total_rating'] += product.get('rating', 0.0)
            brand_stats[brand]['avg_price'] += product.get('price', 0)
            brand_stats[brand]['products'].append(product.get('name', ''))

        # 평균 계산
        for brand, stats in brand_stats.items():
            count = stats['count']
            if count > 0:
                stats['avg_rating'] = stats['total_rating'] / count
                stats['avg_price'] = int(stats['avg_price'] / count)
            else:
                stats['avg_rating'] = 0.0
                stats['avg_price'] = 0

        self.logger.info(f"브랜드 통계 계산 완료: {len(brand_stats)}개 브랜드")

        return brand_stats

    def get_top_brands(self, products: List[Dict], top_n: int = 50, sort_by: str = 'count') -> List[tuple]:
        """
        상위 브랜드 추출

        Args:
            products: 제품 정보 리스트
            top_n: 상위 n개 브랜드
            sort_by: 정렬 기준 ('count', 'reviews', 'rating')

        Returns:
            (브랜드명, 통계) 튜플 리스트
        """
        # 브랜드 통계 계산
        brand_stats = self.get_brand_statistics(products)

        # 정렬 기준에 따라 정렬
        if sort_by == 'count':
            sorted_brands = sorted(
                brand_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
        elif sort_by == 'reviews':
            sorted_brands = sorted(
                brand_stats.items(),
                key=lambda x: x[1]['total_reviews'],
                reverse=True
            )
        elif sort_by == 'rating':
            sorted_brands = sorted(
                brand_stats.items(),
                key=lambda x: (x[1]['avg_rating'], x[1]['count']),
                reverse=True
            )
        else:
            sorted_brands = sorted(
                brand_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

        # 상위 n개 반환
        top_brands = sorted_brands[:top_n]

        self.logger.info(f"상위 {top_n}개 브랜드 추출 완료: {len(top_brands)}개")

        return top_brands

    def filter_by_brands(self, products: List[Dict], brands: List[str]) -> List[Dict]:
        """
        특정 브랜드만 필터링

        Args:
            products: 제품 정보 리스트
            brands: 필터링할 브랜드 리스트

        Returns:
            필터링된 제품 리스트
        """
        # 브랜드명 정규화
        normalized_brands = [self.normalize_brand(b) for b in brands]

        filtered_products = []

        for product in products:
            brand = self.extract_brand(product)
            normalized_brand = self.normalize_brand(brand)

            if normalized_brand in normalized_brands:
                filtered_products.append(product)

        self.logger.info(f"브랜드 필터링 완료: {len(filtered_products)}/{len(products)}개 제품")

        return filtered_products

    def is_user_brand(self, product: Dict) -> bool:
        """
        사용자 지정 브랜드 여부 확인

        Args:
            product: 제품 정보

        Returns:
            사용자 지정 브랜드이면 True
        """
        brand = self.extract_brand(product)

        if not brand:
            return False

        # 정규화된 브랜드명으로 비교
        normalized_brand = self.normalize_brand(brand)
        normalized_user_brands = [self.normalize_brand(b) for b in self.user_brands]

        return normalized_brand in normalized_user_brands

    def get_user_brand_products(self, products: List[Dict]) -> List[Dict]:
        """
        사용자 지정 브랜드 제품만 추출

        Args:
            products: 제품 정보 리스트

        Returns:
            사용자 지정 브랜드 제품 리스트
        """
        user_brand_products = [p for p in products if self.is_user_brand(p)]

        self.logger.info(f"사용자 브랜드 제품 추출 완료: {len(user_brand_products)}개")

        return user_brand_products

    def get_competitor_products(self, products: List[Dict]) -> List[Dict]:
        """
        경쟁사 제품 추출 (사용자 브랜드 제외)

        Args:
            products: 제품 정보 리스트

        Returns:
            경쟁사 제품 리스트
        """
        competitor_products = [p for p in products if not self.is_user_brand(p)]

        self.logger.info(f"경쟁사 제품 추출 완료: {len(competitor_products)}개")

        return competitor_products

    def create_brand_report(self, products: List[Dict], top_n: int = 20) -> Dict:
        """
        브랜드 분석 리포트 생성

        Args:
            products: 제품 정보 리스트
            top_n: 상위 n개 브랜드

        Returns:
            리포트 딕셔너리
        """
        # 전체 통계
        total_products = len(products)
        user_brand_products = self.get_user_brand_products(products)
        competitor_products = self.get_competitor_products(products)

        # 상위 브랜드
        top_brands_by_count = self.get_top_brands(products, top_n, sort_by='count')
        top_brands_by_reviews = self.get_top_brands(products, top_n, sort_by='reviews')

        # 리포트 생성
        report = {
            'summary': {
                'total_products': total_products,
                'user_brand_products': len(user_brand_products),
                'competitor_products': len(competitor_products),
                'user_brand_ratio': len(user_brand_products) / total_products if total_products > 0 else 0,
            },
            'top_brands_by_count': [
                {
                    'rank': idx + 1,
                    'brand': brand,
                    'count': stats['count'],
                    'avg_rating': round(stats['avg_rating'], 2),
                    'avg_price': stats['avg_price'],
                    'total_reviews': stats['total_reviews']
                }
                for idx, (brand, stats) in enumerate(top_brands_by_count)
            ],
            'top_brands_by_reviews': [
                {
                    'rank': idx + 1,
                    'brand': brand,
                    'count': stats['count'],
                    'avg_rating': round(stats['avg_rating'], 2),
                    'avg_price': stats['avg_price'],
                    'total_reviews': stats['total_reviews']
                }
                for idx, (brand, stats) in enumerate(top_brands_by_reviews)
            ],
            'user_brands': {
                brand: {
                    'count': stats['count'],
                    'avg_rating': round(stats['avg_rating'], 2),
                    'avg_price': stats['avg_price'],
                    'total_reviews': stats['total_reviews']
                }
                for brand, stats in self.get_brand_statistics(user_brand_products).items()
            }
        }

        self.logger.info("브랜드 분석 리포트 생성 완료")

        return report
