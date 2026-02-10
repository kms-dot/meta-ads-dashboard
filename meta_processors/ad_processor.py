import logging
from typing import List, Dict
from collections import Counter
from datetime import datetime


class AdProcessor:
    """Meta 광고 데이터 분석 및 처리 클래스"""

    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_ads(self, ads: List[Dict]) -> Dict:
        """
        광고 데이터 종합 분석

        Args:
            ads: 광고 데이터 리스트

        Returns:
            분석 결과 딕셔너리
        """
        if not ads:
            return self._empty_analysis()

        analysis = {
            'summary': self._create_summary(ads),
            'advertiser_stats': self._analyze_advertisers(ads),
            'media_stats': self._analyze_media_types(ads),
            'platform_stats': self._analyze_platforms(ads),
            'timeline_stats': self._analyze_timeline(ads),
            'top_ads': self._get_top_ads(ads),
        }

        self.logger.info(f"광고 분석 완료: {len(ads)}개 광고")

        return analysis

    def _empty_analysis(self) -> Dict:
        """빈 분석 결과 반환"""
        return {
            'summary': {
                'total_ads': 0,
                'unique_advertisers': 0,
                'avg_days_live': 0,
            },
            'advertiser_stats': [],
            'media_stats': {},
            'platform_stats': {},
            'timeline_stats': {},
            'top_ads': [],
        }

    def _create_summary(self, ads: List[Dict]) -> Dict:
        """요약 통계 생성"""
        total_ads = len(ads)

        # 고유 광고주 수
        advertisers = set(ad.get('advertiser', 'Unknown') for ad in ads)
        unique_advertisers = len(advertisers)

        # 평균 라이브 일수
        days_live_list = [ad.get('days_live', 0) for ad in ads if ad.get('days_live', 0) > 0]
        avg_days_live = sum(days_live_list) / len(days_live_list) if days_live_list else 0

        # 미디어 타입별 개수
        media_types = Counter(ad.get('media_type', 'unknown') for ad in ads)

        # 플랫폼별 개수
        platform_counts = Counter()
        for ad in ads:
            platforms = ad.get('platforms', [])
            for platform in platforms:
                platform_counts[platform] += 1

        return {
            'total_ads': total_ads,
            'unique_advertisers': unique_advertisers,
            'avg_days_live': round(avg_days_live, 1),
            'media_type_counts': dict(media_types),
            'platform_counts': dict(platform_counts),
        }

    def _analyze_advertisers(self, ads: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        광고주별 분석

        Args:
            ads: 광고 데이터 리스트
            top_n: 상위 n개 광고주

        Returns:
            광고주별 통계 리스트
        """
        advertiser_stats = {}

        for ad in ads:
            advertiser = ad.get('advertiser', 'Unknown')

            if advertiser not in advertiser_stats:
                advertiser_stats[advertiser] = {
                    'advertiser': advertiser,
                    'ad_count': 0,
                    'total_days_live': 0,
                    'avg_days_live': 0,
                    'media_types': Counter(),
                    'platforms': Counter(),
                    'ads': []
                }

            stats = advertiser_stats[advertiser]
            stats['ad_count'] += 1
            stats['total_days_live'] += ad.get('days_live', 0)
            stats['media_types'][ad.get('media_type', 'unknown')] += 1

            # 플랫폼 집계
            for platform in ad.get('platforms', []):
                stats['platforms'][platform] += 1

            stats['ads'].append({
                'ad_id': ad.get('ad_id', ''),
                'ad_text': ad.get('ad_text', '')[:100],  # 첫 100자만
                'days_live': ad.get('days_live', 0),
                'url': ad.get('ad_library_url', '')
            })

        # 평균 계산
        for advertiser, stats in advertiser_stats.items():
            if stats['ad_count'] > 0:
                stats['avg_days_live'] = round(stats['total_days_live'] / stats['ad_count'], 1)
            stats['media_types'] = dict(stats['media_types'])
            stats['platforms'] = dict(stats['platforms'])

        # 광고 개수로 정렬
        sorted_stats = sorted(
            advertiser_stats.values(),
            key=lambda x: x['ad_count'],
            reverse=True
        )

        return sorted_stats[:top_n]

    def _analyze_media_types(self, ads: List[Dict]) -> Dict:
        """미디어 타입별 분석"""
        media_stats = {}

        for ad in ads:
            media_type = ad.get('media_type', 'unknown')

            if media_type not in media_stats:
                media_stats[media_type] = {
                    'count': 0,
                    'total_days_live': 0,
                    'avg_days_live': 0,
                }

            media_stats[media_type]['count'] += 1
            media_stats[media_type]['total_days_live'] += ad.get('days_live', 0)

        # 평균 계산
        for media_type, stats in media_stats.items():
            if stats['count'] > 0:
                stats['avg_days_live'] = round(stats['total_days_live'] / stats['count'], 1)

        return media_stats

    def _analyze_platforms(self, ads: List[Dict]) -> Dict:
        """플랫폼별 분석"""
        platform_stats = {}

        for ad in ads:
            platforms = ad.get('platforms', [])

            for platform in platforms:
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        'count': 0,
                        'advertisers': set(),
                        'media_types': Counter(),
                    }

                platform_stats[platform]['count'] += 1
                platform_stats[platform]['advertisers'].add(ad.get('advertiser', 'Unknown'))
                platform_stats[platform]['media_types'][ad.get('media_type', 'unknown')] += 1

        # set을 count로 변환
        for platform, stats in platform_stats.items():
            stats['unique_advertisers'] = len(stats['advertisers'])
            stats.pop('advertisers')
            stats['media_types'] = dict(stats['media_types'])

        return platform_stats

    def _analyze_timeline(self, ads: List[Dict]) -> Dict:
        """시간대별 분석"""
        timeline_stats = {
            'very_recent': 0,      # 0-7일
            'recent': 0,           # 8-30일
            'medium': 0,           # 31-90일
            'long': 0,             # 91-180일
            'very_long': 0,        # 181일 이상
        }

        for ad in ads:
            days_live = ad.get('days_live', 0)

            if days_live <= 7:
                timeline_stats['very_recent'] += 1
            elif days_live <= 30:
                timeline_stats['recent'] += 1
            elif days_live <= 90:
                timeline_stats['medium'] += 1
            elif days_live <= 180:
                timeline_stats['long'] += 1
            else:
                timeline_stats['very_long'] += 1

        return timeline_stats

    def _get_top_ads(self, ads: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        상위 광고 추출 (라이브 일수 기준)

        Args:
            ads: 광고 데이터 리스트
            top_n: 상위 n개

        Returns:
            상위 광고 리스트
        """
        # 라이브 일수로 정렬
        sorted_ads = sorted(
            ads,
            key=lambda x: x.get('days_live', 0),
            reverse=True
        )

        top_ads = []
        for ad in sorted_ads[:top_n]:
            top_ads.append({
                'rank': len(top_ads) + 1,
                'advertiser': ad.get('advertiser', 'Unknown'),
                'ad_text': ad.get('ad_text', '')[:150],
                'days_live': ad.get('days_live', 0),
                'start_date': ad.get('start_date', ''),
                'media_type': ad.get('media_type', 'unknown'),
                'platforms': ad.get('platforms', []),
                'url': ad.get('ad_library_url', '')
            })

        return top_ads

    def filter_by_advertiser(self, ads: List[Dict], advertisers: List[str]) -> List[Dict]:
        """
        특정 광고주로 필터링

        Args:
            ads: 광고 데이터 리스트
            advertisers: 광고주 리스트

        Returns:
            필터링된 광고 리스트
        """
        filtered = [
            ad for ad in ads
            if ad.get('advertiser', '') in advertisers
        ]

        self.logger.info(f"광고주 필터링 완료: {len(filtered)}/{len(ads)}개")

        return filtered

    def filter_by_media_type(self, ads: List[Dict], media_types: List[str]) -> List[Dict]:
        """
        미디어 타입으로 필터링

        Args:
            ads: 광고 데이터 리스트
            media_types: 미디어 타입 리스트 (예: ['video', 'image'])

        Returns:
            필터링된 광고 리스트
        """
        filtered = [
            ad for ad in ads
            if ad.get('media_type', '') in media_types
        ]

        self.logger.info(f"미디어 타입 필터링 완료: {len(filtered)}/{len(ads)}개")

        return filtered

    def filter_by_days_live(self, ads: List[Dict], min_days: int = 0, max_days: int = None) -> List[Dict]:
        """
        라이브 일수로 필터링

        Args:
            ads: 광고 데이터 리스트
            min_days: 최소 일수
            max_days: 최대 일수 (None이면 무제한)

        Returns:
            필터링된 광고 리스트
        """
        filtered = []

        for ad in ads:
            days_live = ad.get('days_live', 0)

            if days_live < min_days:
                continue

            if max_days is not None and days_live > max_days:
                continue

            filtered.append(ad)

        self.logger.info(f"라이브 일수 필터링 완료: {len(filtered)}/{len(ads)}개")

        return filtered

    def filter_by_platform(self, ads: List[Dict], platforms: List[str]) -> List[Dict]:
        """
        플랫폼으로 필터링

        Args:
            ads: 광고 데이터 리스트
            platforms: 플랫폼 리스트 (예: ['Facebook', 'Instagram'])

        Returns:
            필터링된 광고 리스트
        """
        filtered = []

        for ad in ads:
            ad_platforms = ad.get('platforms', [])

            # 지정한 플랫폼 중 하나라도 포함하면 추가
            if any(platform in ad_platforms for platform in platforms):
                filtered.append(ad)

        self.logger.info(f"플랫폼 필터링 완료: {len(filtered)}/{len(ads)}개")

        return filtered

    def sort_by_days_live(self, ads: List[Dict], reverse: bool = True) -> List[Dict]:
        """라이브 일수로 정렬"""
        return sorted(ads, key=lambda x: x.get('days_live', 0), reverse=reverse)

    def group_by_advertiser(self, ads: List[Dict]) -> Dict[str, List[Dict]]:
        """광고주별로 그룹화"""
        grouped = {}

        for ad in ads:
            advertiser = ad.get('advertiser', 'Unknown')

            if advertiser not in grouped:
                grouped[advertiser] = []

            grouped[advertiser].append(ad)

        return grouped

    def create_report(self, ads: List[Dict], query: str = '') -> Dict:
        """
        종합 리포트 생성

        Args:
            ads: 광고 데이터 리스트
            query: 검색 쿼리

        Returns:
            리포트 딕셔너리
        """
        report = {
            'query': query,
            'crawl_date': datetime.now().isoformat(),
            'total_ads': len(ads),
            'analysis': self.analyze_ads(ads),
            'ads_data': ads,
        }

        self.logger.info("종합 리포트 생성 완료")

        return report
