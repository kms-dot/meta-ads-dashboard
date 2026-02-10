import logging
from typing import List, Dict
from datetime import datetime
from .supabase_client import get_supabase_client


class ProductRepository:
    """쇼핑몰 제품 데이터 저장소"""

    def __init__(self):
        """초기화"""
        self.client = get_supabase_client()
        self.table = 'products'
        self.logger = logging.getLogger(self.__class__.__name__)

    def save_product(self, product_data: Dict, category: str) -> Dict:
        """
        제품 데이터 저장

        Args:
            product_data: 제품 데이터 딕셔너리
            category: 카테고리명

        Returns:
            저장된 데이터
        """
        try:
            insert_data = {
                'category': category,
                'name': product_data.get('name'),
                'brand': product_data.get('brand'),
                'price': product_data.get('price', 0),
                'original_price': product_data.get('original_price'),
                'discount_rate': product_data.get('discount_rate', 0),
                'review_count': product_data.get('review_count', 0),
                'rating': product_data.get('rating', 0),
                'link': product_data.get('link'),
                'image_url': product_data.get('image_url'),
                'platform': product_data.get('platform'),
                'keyword': product_data.get('keyword'),
                'rank': product_data.get('rank'),
                'is_sale': product_data.get('is_sale', False),
                'is_best': product_data.get('is_best', False),
                'is_rocket': product_data.get('is_rocket', False),
            }

            result = self.client.table(self.table).insert(insert_data).execute()

            return result.data[0] if result.data else {}

        except Exception as e:
            self.logger.error(f"제품 저장 중 오류: {e}")
            return {}

    def save_products_batch(self, products: List[Dict], category: str) -> Dict:
        """
        여러 제품을 일괄 저장

        Args:
            products: 제품 데이터 리스트
            category: 카테고리명

        Returns:
            저장 결과 통계
        """
        stats = {
            'total': len(products),
            'inserted': 0,
            'failed': 0
        }

        for product in products:
            try:
                result = self.save_product(product, category)
                if result:
                    stats['inserted'] += 1
            except Exception as e:
                self.logger.error(f"제품 저장 실패: {e}")
                stats['failed'] += 1

        self.logger.info(
            f"일괄 저장 완료 - 총: {stats['total']}, "
            f"성공: {stats['inserted']}, 실패: {stats['failed']}"
        )

        return stats

    def get_products_by_category(
        self,
        category: str,
        platform: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        카테고리별 제품 조회

        Args:
            category: 카테고리명
            platform: 플랫폼 (None이면 전체)
            limit: 최대 개수

        Returns:
            제품 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('category', category)

            if platform:
                query = query.eq('platform', platform)

            result = query.order('collected_at', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"제품 조회 중 오류: {e}")
            return []

    def get_products_by_brand(self, brand: str, category: str = None) -> List[Dict]:
        """
        브랜드별 제품 조회

        Args:
            brand: 브랜드명
            category: 카테고리명 (선택사항)

        Returns:
            제품 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('brand', brand)

            if category:
                query = query.eq('category', category)

            result = query.order('rating', desc=True).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"브랜드별 제품 조회 중 오류: {e}")
            return []

    def delete_old_products(self, days: int = 30) -> int:
        """
        오래된 제품 데이터 삭제

        Args:
            days: 삭제 기준 일수

        Returns:
            삭제된 제품 수
        """
        try:
            from datetime import timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.client.table(self.table).delete().lt(
                'collected_at', cutoff_date
            ).execute()

            count = len(result.data) if result.data else 0
            self.logger.info(f"{days}일 이전 제품 {count}개 삭제")

            return count

        except Exception as e:
            self.logger.error(f"제품 삭제 중 오류: {e}")
            return 0
