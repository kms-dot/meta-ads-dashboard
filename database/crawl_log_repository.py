import logging
from typing import List, Dict, Optional
from datetime import datetime
from .supabase_client import get_supabase_client


class CrawlLogRepository:
    """크롤링 이력 저장소"""

    def __init__(self):
        """초기화"""
        self.client = get_supabase_client()
        self.table = 'crawl_logs'
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_log_id: Optional[str] = None

    def start_crawl_log(
        self,
        crawl_type: str,
        category: str = None,
        platform: str = None,
        query: str = None
    ) -> str:
        """
        크롤링 시작 로그 생성

        Args:
            crawl_type: 크롤링 타입 ('ecommerce', 'meta_ads')
            category: 카테고리명
            platform: 플랫폼
            query: 검색 쿼리

        Returns:
            로그 ID
        """
        try:
            insert_data = {
                'crawl_type': crawl_type,
                'category': category,
                'platform': platform,
                'query': query,
                'status': 'running',
                'started_at': datetime.now().isoformat()
            }

            result = self.client.table(self.table).insert(insert_data).execute()

            if result.data:
                log_id = result.data[0]['id']
                self._current_log_id = log_id
                self.logger.info(f"크롤링 로그 시작: {log_id}")
                return log_id

            return ''

        except Exception as e:
            self.logger.error(f"크롤링 로그 시작 중 오류: {e}")
            return ''

    def complete_crawl_log(
        self,
        log_id: str,
        items_collected: int = 0,
        items_new: int = 0,
        items_updated: int = 0,
        status: str = 'success',
        error_message: str = None
    ) -> Dict:
        """
        크롤링 완료 로그 업데이트

        Args:
            log_id: 로그 ID
            items_collected: 수집된 아이템 수
            items_new: 신규 아이템 수
            items_updated: 업데이트된 아이템 수
            status: 상태 ('success', 'failed', 'partial')
            error_message: 에러 메시지

        Returns:
            업데이트된 로그 데이터
        """
        try:
            # 시작 시간 조회
            start_log = self.client.table(self.table).select('started_at').eq(
                'id', log_id
            ).execute()

            duration_seconds = 0
            if start_log.data:
                started_at = datetime.fromisoformat(start_log.data[0]['started_at'].replace('Z', '+00:00'))
                completed_at = datetime.now()
                duration_seconds = int((completed_at - started_at).total_seconds())

            # 로그 업데이트
            update_data = {
                'items_collected': items_collected,
                'items_new': items_new,
                'items_updated': items_updated,
                'status': status,
                'error_message': error_message,
                'completed_at': datetime.now().isoformat(),
                'duration_seconds': duration_seconds
            }

            result = self.client.table(self.table).update(update_data).eq(
                'id', log_id
            ).execute()

            self.logger.info(
                f"크롤링 로그 완료: {log_id} - "
                f"{items_collected}개 수집, {duration_seconds}초 소요"
            )

            return result.data[0] if result.data else {}

        except Exception as e:
            self.logger.error(f"크롤링 로그 완료 중 오류: {e}")
            return {}

    def fail_crawl_log(self, log_id: str, error_message: str) -> Dict:
        """
        크롤링 실패 로그

        Args:
            log_id: 로그 ID
            error_message: 에러 메시지

        Returns:
            업데이트된 로그 데이터
        """
        return self.complete_crawl_log(
            log_id=log_id,
            status='failed',
            error_message=error_message
        )

    def get_recent_logs(
        self,
        crawl_type: str = None,
        category: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        최근 크롤링 로그 조회

        Args:
            crawl_type: 크롤링 타입 (None이면 전체)
            category: 카테고리명 (None이면 전체)
            limit: 최대 개수

        Returns:
            로그 리스트
        """
        try:
            query = self.client.table(self.table).select('*')

            if crawl_type:
                query = query.eq('crawl_type', crawl_type)

            if category:
                query = query.eq('category', category)

            result = query.order('started_at', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"크롤링 로그 조회 중 오류: {e}")
            return []

    def get_crawl_stats(self, crawl_type: str = None, days: int = 7) -> Dict:
        """
        크롤링 통계 조회

        Args:
            crawl_type: 크롤링 타입 (None이면 전체)
            days: 최근 n일

        Returns:
            통계 딕셔너리
        """
        try:
            from datetime import timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = self.client.table(self.table).select('*').gt('started_at', cutoff_date)

            if crawl_type:
                query = query.eq('crawl_type', crawl_type)

            result = query.execute()

            if not result.data:
                return {
                    'total_crawls': 0,
                    'success_crawls': 0,
                    'failed_crawls': 0,
                    'total_items_collected': 0,
                    'avg_duration_seconds': 0
                }

            logs = result.data

            stats = {
                'total_crawls': len(logs),
                'success_crawls': sum(1 for log in logs if log.get('status') == 'success'),
                'failed_crawls': sum(1 for log in logs if log.get('status') == 'failed'),
                'total_items_collected': sum(log.get('items_collected', 0) for log in logs),
                'avg_duration_seconds': (
                    sum(log.get('duration_seconds', 0) for log in logs) / len(logs)
                    if logs else 0
                )
            }

            return stats

        except Exception as e:
            self.logger.error(f"크롤링 통계 조회 중 오류: {e}")
            return {}

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        if self._current_log_id:
            if exc_type is not None:
                # 예외 발생 시 실패 로그
                error_message = str(exc_val) if exc_val else "Unknown error"
                self.fail_crawl_log(self._current_log_id, error_message)
            # _current_log_id 초기화
            self._current_log_id = None
