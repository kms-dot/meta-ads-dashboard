import logging
from typing import List, Dict, Optional
from datetime import datetime
from .supabase_client import get_supabase_client


class KeywordRepository:
    """키워드 데이터 저장소"""

    def __init__(self):
        """초기화"""
        self.client = get_supabase_client()
        self.table = 'keywords'
        self.logger = logging.getLogger(self.__class__.__name__)

    def save_keyword(
        self,
        category: str,
        keyword: str,
        keyword_type: str,
        source: str = 'user_provided',
        priority: int = 0
    ) -> Dict:
        """
        키워드 저장

        Args:
            category: 카테고리명
            keyword: 키워드
            keyword_type: 키워드 타입 ('product_type', 'brand', 'function')
            source: 출처
            priority: 우선순위

        Returns:
            저장된 데이터
        """
        try:
            # 중복 체크
            existing = self.client.table(self.table).select('id').eq(
                'category', category
            ).eq('keyword', keyword).eq('keyword_type', keyword_type).execute()

            if existing.data:
                # 이미 존재하면 활성화 및 우선순위 업데이트
                result = self.client.table(self.table).update({
                    'is_active': True,
                    'search_priority': priority,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', existing.data[0]['id']).execute()

                self.logger.debug(f"키워드 업데이트: {keyword}")
                return result.data[0] if result.data else {}
            else:
                # 신규 저장
                insert_data = {
                    'category': category,
                    'keyword': keyword,
                    'keyword_type': keyword_type,
                    'source': source,
                    'search_priority': priority,
                    'is_active': True
                }

                result = self.client.table(self.table).insert(insert_data).execute()

                self.logger.debug(f"키워드 신규 저장: {keyword}")
                return result.data[0] if result.data else {}

        except Exception as e:
            self.logger.error(f"키워드 저장 중 오류: {e}")
            return {}

    def save_keywords_batch(
        self,
        category: str,
        keywords_dict: Dict[str, List[str]],
        source: str = 'user_provided'
    ) -> Dict:
        """
        여러 키워드를 일괄 저장

        Args:
            category: 카테고리명
            keywords_dict: {
                'product_types': [...],
                'brands': [...],
                'functions': [...]
            }
            source: 출처

        Returns:
            저장 결과 통계
        """
        stats = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'failed': 0
        }

        # 제품 타입 키워드
        product_types = keywords_dict.get('product_types', [])
        for idx, keyword in enumerate(product_types):
            stats['total'] += 1
            try:
                priority = len(product_types) - idx  # 앞쪽 키워드가 높은 우선순위
                self.save_keyword(category, keyword, 'product_type', source, priority)
                stats['inserted'] += 1
            except Exception as e:
                self.logger.error(f"키워드 저장 실패: {keyword} - {e}")
                stats['failed'] += 1

        # 브랜드 키워드
        brands = keywords_dict.get('brands', [])
        for idx, keyword in enumerate(brands):
            stats['total'] += 1
            try:
                priority = len(brands) - idx + 100  # 브랜드는 더 높은 우선순위
                self.save_keyword(category, keyword, 'brand', source, priority)
                stats['inserted'] += 1
            except Exception as e:
                self.logger.error(f"브랜드 저장 실패: {keyword} - {e}")
                stats['failed'] += 1

        # 기능 키워드
        functions = keywords_dict.get('functions', [])
        for idx, keyword in enumerate(functions):
            stats['total'] += 1
            try:
                priority = len(functions) - idx
                self.save_keyword(category, keyword, 'function', source, priority)
                stats['inserted'] += 1
            except Exception as e:
                self.logger.error(f"기능 키워드 저장 실패: {keyword} - {e}")
                stats['failed'] += 1

        self.logger.info(
            f"일괄 저장 완료 - 총: {stats['total']}, "
            f"성공: {stats['inserted']}, 실패: {stats['failed']}"
        )

        return stats

    def get_active_keywords(
        self,
        category: str = None,
        keyword_type: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        활성 키워드 조회

        Args:
            category: 카테고리명 (None이면 전체)
            keyword_type: 키워드 타입 (None이면 전체)
            limit: 최대 개수

        Returns:
            키워드 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('is_active', True)

            if category:
                query = query.eq('category', category)

            if keyword_type:
                query = query.eq('keyword_type', keyword_type)

            result = query.order('search_priority', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"활성 키워드 조회 중 오류: {e}")
            return []

    def get_keywords_by_category(self, category: str) -> Dict[str, List[str]]:
        """
        카테고리별 키워드 조회 (타입별로 그룹화)

        Args:
            category: 카테고리명

        Returns:
            {
                'product_types': [...],
                'brands': [...],
                'functions': [...]
            }
        """
        try:
            keywords = self.get_active_keywords(category=category)

            result = {
                'product_types': [],
                'brands': [],
                'functions': []
            }

            for kw in keywords:
                keyword_type = kw.get('keyword_type')
                keyword_value = kw.get('keyword')

                if keyword_type == 'product_type':
                    result['product_types'].append(keyword_value)
                elif keyword_type == 'brand':
                    result['brands'].append(keyword_value)
                elif keyword_type == 'function':
                    result['functions'].append(keyword_value)

            return result

        except Exception as e:
            self.logger.error(f"카테고리별 키워드 조회 중 오류: {e}")
            return {'product_types': [], 'brands': [], 'functions': []}

    def update_search_stats(
        self,
        keyword_id: str,
        products_found: int = 0,
        ads_found: int = 0
    ) -> Dict:
        """
        검색 통계 업데이트

        Args:
            keyword_id: 키워드 ID
            products_found: 발견된 제품 수
            ads_found: 발견된 광고 수

        Returns:
            업데이트된 데이터
        """
        try:
            # 현재 통계 조회
            current = self.client.table(self.table).select(
                'search_count, total_products_found, total_ads_found'
            ).eq('id', keyword_id).execute()

            if not current.data:
                return {}

            current_data = current.data[0]

            # 통계 업데이트
            update_data = {
                'search_count': current_data.get('search_count', 0) + 1,
                'total_products_found': current_data.get('total_products_found', 0) + products_found,
                'total_ads_found': current_data.get('total_ads_found', 0) + ads_found,
                'last_searched': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            result = self.client.table(self.table).update(update_data).eq(
                'id', keyword_id
            ).execute()

            return result.data[0] if result.data else {}

        except Exception as e:
            self.logger.error(f"검색 통계 업데이트 중 오류: {e}")
            return {}

    def deactivate_all_by_category(self, category: str) -> int:
        """
        카테고리의 모든 키워드 비활성화

        Args:
            category: 카테고리명

        Returns:
            비활성화된 키워드 수
        """
        try:
            result = self.client.table(self.table).update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('category', category).eq('is_active', True).execute()

            count = len(result.data) if result.data else 0
            self.logger.info(f"{category} 카테고리 키워드 {count}개 비활성화")

            return count

        except Exception as e:
            self.logger.error(f"키워드 비활성화 중 오류: {e}")
            return 0

    def get_top_performing_keywords(
        self,
        category: str = None,
        metric: str = 'products',
        limit: int = 20
    ) -> List[Dict]:
        """
        성과가 좋은 키워드 조회

        Args:
            category: 카테고리명 (None이면 전체)
            metric: 정렬 기준 ('products' 또는 'ads')
            limit: 최대 개수

        Returns:
            키워드 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('is_active', True)

            if category:
                query = query.eq('category', category)

            # 정렬 기준
            if metric == 'ads':
                order_column = 'total_ads_found'
            else:
                order_column = 'total_products_found'

            result = query.order(order_column, desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"상위 성과 키워드 조회 중 오류: {e}")
            return []

    def delete_keyword(self, keyword_id: str) -> bool:
        """
        키워드 삭제

        Args:
            keyword_id: 키워드 ID

        Returns:
            삭제 성공 여부
        """
        try:
            result = self.client.table(self.table).delete().eq('id', keyword_id).execute()

            success = len(result.data) > 0 if result.data else False

            if success:
                self.logger.info(f"키워드 삭제 완료: {keyword_id}")

            return success

        except Exception as e:
            self.logger.error(f"키워드 삭제 중 오류: {e}")
            return False
