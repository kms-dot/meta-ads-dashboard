import logging
from typing import List, Dict, Optional
from datetime import datetime
from .supabase_client import get_supabase_client


class AdRepository:
    """Meta 광고 데이터 저장소"""

    def __init__(self):
        """초기화"""
        self.client = get_supabase_client()
        self.table = 'ads'
        self.logger = logging.getLogger(self.__class__.__name__)

    def save_ad(self, ad_data: Dict, category: str) -> Dict:
        """
        광고 데이터를 Supabase에 저장

        Args:
            ad_data: 광고 데이터 딕셔너리
            category: 카테고리명

        Returns:
            저장된 데이터 또는 업데이트된 데이터
        """
        try:
            ad_library_url = ad_data.get('ad_library_url')

            if not ad_library_url:
                self.logger.warning("ad_library_url이 없는 데이터는 저장하지 않습니다")
                return {}

            # 중복 체크
            existing = self.client.table(self.table).select('id, ad_library_url').eq(
                'ad_library_url', ad_library_url
            ).execute()

            if existing.data:
                # 이미 존재하면 업데이트
                result = self._update_existing_ad(existing.data[0]['id'], ad_data)
                self.logger.debug(f"광고 업데이트: {ad_data.get('advertiser')}")
                return result
            else:
                # 신규 저장
                result = self._insert_new_ad(ad_data, category)
                self.logger.debug(f"광고 신규 저장: {ad_data.get('advertiser')}")
                return result

        except Exception as e:
            self.logger.error(f"광고 저장 중 오류: {e}")
            return {}

    def _insert_new_ad(self, ad_data: Dict, category: str) -> Dict:
        """신규 광고 저장"""
        insert_data = {
            'category': category,
            'advertiser': ad_data.get('advertiser', 'Unknown'),
            'ad_id': ad_data.get('ad_id'),
            'ad_text': ad_data.get('ad_text'),
            'thumbnail_url': ad_data.get('thumbnail_url'),
            'video_url': ad_data.get('video_url'),
            'media_type': ad_data.get('media_type', 'unknown'),
            'platforms': ad_data.get('platforms', []),
            'ad_library_url': ad_data.get('ad_library_url'),
            'days_live': ad_data.get('days_live', 0),
            'start_date': self._parse_date(ad_data.get('start_date')),
            'impression_text': ad_data.get('impression_text'),
            'is_active': True,
            'query': ad_data.get('query'),
            'rank': ad_data.get('rank'),
            'crawl_date': ad_data.get('crawl_date'),
        }

        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else {}

    def _update_existing_ad(self, ad_id: str, ad_data: Dict) -> Dict:
        """기존 광고 업데이트"""
        update_data = {
            'days_live': ad_data.get('days_live', 0),
            'last_checked': datetime.now().isoformat(),
            'is_active': True,  # 크롤링에서 발견되었으므로 활성화
            'impression_text': ad_data.get('impression_text'),
        }

        # 광고 텍스트가 변경되었을 수 있음
        if ad_data.get('ad_text'):
            update_data['ad_text'] = ad_data.get('ad_text')

        result = self.client.table(self.table).update(update_data).eq('id', ad_id).execute()
        return result.data[0] if result.data else {}

    def save_ads_batch(self, ads: List[Dict], category: str) -> Dict:
        """
        여러 광고를 일괄 저장

        Args:
            ads: 광고 데이터 리스트
            category: 카테고리명

        Returns:
            저장 결과 통계
        """
        stats = {
            'total': len(ads),
            'inserted': 0,
            'updated': 0,
            'failed': 0
        }

        for ad in ads:
            try:
                result = self.save_ad(ad, category)
                if result:
                    # created_at과 updated_at을 비교하여 신규/업데이트 구분
                    # (실제로는 insert/update 구분이 어려우므로 간단히 처리)
                    stats['inserted'] += 1
            except Exception as e:
                self.logger.error(f"광고 저장 실패: {e}")
                stats['failed'] += 1

        self.logger.info(
            f"일괄 저장 완료 - 총: {stats['total']}, "
            f"성공: {stats['inserted']}, 실패: {stats['failed']}"
        )

        return stats

    def get_ads_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        카테고리별 광고 조회

        Args:
            category: 카테고리명
            limit: 최대 개수

        Returns:
            광고 리스트
        """
        try:
            result = self.client.table(self.table).select('*').eq(
                'category', category
            ).order('collected_at', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"광고 조회 중 오류: {e}")
            return []

    def get_active_ads(self, category: str = None, limit: int = 100) -> List[Dict]:
        """
        활성 광고 조회

        Args:
            category: 카테고리명 (None이면 전체)
            limit: 최대 개수

        Returns:
            활성 광고 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('is_active', True)

            if category:
                query = query.eq('category', category)

            result = query.order('days_live', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"활성 광고 조회 중 오류: {e}")
            return []

    def get_ads_by_advertiser(self, advertiser: str, category: str = None) -> List[Dict]:
        """
        광고주별 광고 조회

        Args:
            advertiser: 광고주명
            category: 카테고리명 (선택사항)

        Returns:
            광고 리스트
        """
        try:
            query = self.client.table(self.table).select('*').eq('advertiser', advertiser)

            if category:
                query = query.eq('category', category)

            result = query.order('collected_at', desc=True).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"광고주별 광고 조회 중 오류: {e}")
            return []

    def get_top_ads_by_days_live(self, category: str, limit: int = 20) -> List[Dict]:
        """
        라이브 일수 상위 광고 조회

        Args:
            category: 카테고리명
            limit: 최대 개수

        Returns:
            상위 광고 리스트
        """
        try:
            result = self.client.table(self.table).select('*').eq(
                'category', category
            ).eq('is_active', True).order('days_live', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"상위 광고 조회 중 오류: {e}")
            return []

    def deactivate_old_ads(self, days_threshold: int = 90) -> int:
        """
        오래된 광고 비활성화

        Args:
            days_threshold: 비활성화 기준 일수

        Returns:
            비활성화된 광고 수
        """
        try:
            result = self.client.table(self.table).update({
                'is_active': False
            }).gt('days_live', days_threshold).eq('is_active', True).execute()

            count = len(result.data) if result.data else 0
            self.logger.info(f"{count}개 광고 비활성화 (기준: {days_threshold}일 이상)")

            return count

        except Exception as e:
            self.logger.error(f"광고 비활성화 중 오류: {e}")
            return 0

    def get_advertiser_stats(self, category: str) -> List[Dict]:
        """
        광고주별 통계 조회

        Args:
            category: 카테고리명

        Returns:
            광고주별 통계 리스트
        """
        try:
            # Supabase에서 집계 쿼리 실행
            # 참고: Supabase는 PostgreSQL 집계 함수를 지원하지만,
            # Python SDK에서는 직접 SQL을 실행해야 할 수 있음

            # 간단한 방법: 데이터를 가져와서 Python에서 집계
            result = self.client.table(self.table).select(
                'advertiser, days_live, is_active'
            ).eq('category', category).execute()

            if not result.data:
                return []

            # 광고주별 집계
            stats_dict = {}
            for ad in result.data:
                advertiser = ad.get('advertiser', 'Unknown')

                if advertiser not in stats_dict:
                    stats_dict[advertiser] = {
                        'advertiser': advertiser,
                        'ad_count': 0,
                        'total_days_live': 0,
                        'active_ads': 0
                    }

                stats_dict[advertiser]['ad_count'] += 1
                stats_dict[advertiser]['total_days_live'] += ad.get('days_live', 0)

                if ad.get('is_active'):
                    stats_dict[advertiser]['active_ads'] += 1

            # 평균 계산
            stats_list = []
            for advertiser, stats in stats_dict.items():
                stats['avg_days_live'] = (
                    stats['total_days_live'] / stats['ad_count']
                    if stats['ad_count'] > 0 else 0
                )
                stats_list.append(stats)

            # 광고 수로 정렬
            stats_list.sort(key=lambda x: x['ad_count'], reverse=True)

            return stats_list

        except Exception as e:
            self.logger.error(f"광고주 통계 조회 중 오류: {e}")
            return []

    def delete_ads_by_category(self, category: str) -> int:
        """
        카테고리별 광고 삭제

        Args:
            category: 카테고리명

        Returns:
            삭제된 광고 수
        """
        try:
            result = self.client.table(self.table).delete().eq('category', category).execute()

            count = len(result.data) if result.data else 0
            self.logger.info(f"{category} 카테고리 광고 {count}개 삭제")

            return count

        except Exception as e:
            self.logger.error(f"광고 삭제 중 오류: {e}")
            return 0

    def _parse_date(self, date_str: str) -> Optional[str]:
        """날짜 문자열을 ISO 형식으로 변환"""
        if not date_str:
            return None

        try:
            import re
            from datetime import datetime

            # 한국어 날짜 패턴: "2024년 12월 15일"
            match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', date_str)
            if match:
                year, month, day = match.groups()
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.date().isoformat()

            # 이미 ISO 형식인 경우
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return date_str

        except Exception as e:
            self.logger.debug(f"날짜 파싱 실패: {date_str} - {e}")

        return None
