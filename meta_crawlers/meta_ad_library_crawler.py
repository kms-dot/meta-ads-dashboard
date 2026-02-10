import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote
from selenium.webdriver.common.by import By
from .base_facebook_crawler import BaseFacebookCrawler


class MetaAdLibraryCrawler(BaseFacebookCrawler):
    """Meta 광고 라이브러리 크롤러"""

    BASE_URL = "https://www.facebook.com/ads/library"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "meta_ad_library"

        # 필터 키워드 로드
        self.filter_keywords = self._load_filter_keywords()
        self.date_patterns = self._load_date_patterns()

    def _load_filter_keywords(self) -> Dict:
        """필터 키워드 로드"""
        import json
        try:
            with open('config/meta_selectors.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('filter_keywords', {})
        except:
            return {
                'low_impression': ['적음', 'low', 'fewer', 'less'],
                'active_status': ['게재 중', 'active', 'running', 'live'],
                'inactive_status': ['종료', 'ended', 'inactive', 'stopped']
            }

    def _load_date_patterns(self) -> Dict:
        """날짜 패턴 로드"""
        import json
        try:
            with open('config/meta_selectors.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('date_patterns', {})
        except:
            return {
                'korean': r'(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일',
                'english': r'(?P<month>\w+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})',
                'iso': r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
            }

    def crawl(self, query: str, max_ads: int = 100, country: str = 'KR') -> List[Dict]:
        """
        Meta 광고 라이브러리에서 광고 검색 및 크롤링

        Args:
            query: 검색 키워드
            max_ads: 수집할 최대 광고 수
            country: 국가 코드 (기본값: KR)

        Returns:
            광고 데이터 리스트
        """
        self.logger.info(f"Meta 광고 라이브러리 크롤링 시작: {query}")

        # URL 생성
        search_url = self._build_search_url(query, country)
        self.logger.info(f"검색 URL: {search_url}")

        # 페이지 접속
        try:
            self.driver.get(search_url)
            self.random_delay(3, 5)
        except Exception as e:
            self.logger.error(f"페이지 로드 실패: {e}")
            return []

        # 페이지 로드 대기
        self.wait_for_element(self.selectors.get('ad_card', []), timeout=15)

        ads_data = []
        collected = 0
        scroll_count = 0
        no_new_ads_count = 0

        while collected < max_ads and scroll_count < self.max_scrolls:
            # 광고 카드 찾기
            ad_cards = self._find_ad_cards()

            if not ad_cards:
                self.logger.warning("광고 카드를 찾을 수 없습니다")
                break

            self.logger.info(f"발견된 광고 카드 수: {len(ad_cards)}")

            # 새로운 광고만 처리
            previous_count = len(ads_data)

            for idx, ad_card in enumerate(ad_cards):
                if collected >= max_ads:
                    break

                try:
                    # 광고 정보 추출
                    ad_info = self.extract_ad_info(ad_card)

                    if not ad_info:
                        continue

                    # 중복 체크 (광고 링크 기준)
                    if any(ad.get('ad_library_url') == ad_info.get('ad_library_url') for ad in ads_data):
                        continue

                    # 필터링
                    if self.is_low_impression(ad_card):
                        self.logger.debug(f"노출수 적음 필터링: {ad_info.get('advertiser')}")
                        continue

                    # 라이브 여부 확인 (선택사항)
                    # if not self.is_active_ad(ad_card):
                    #     continue

                    # 데이터 추가
                    ad_info['query'] = query
                    ad_info['platform'] = self.platform_name
                    ad_info['rank'] = collected + 1
                    ad_info['crawl_date'] = datetime.now().isoformat()

                    ads_data.append(ad_info)
                    collected += 1

                    self.logger.debug(f"광고 수집 완료 ({collected}/{max_ads}): {ad_info.get('advertiser')}")

                except Exception as e:
                    self.logger.warning(f"광고 정보 추출 실패 (인덱스 {idx}): {e}")
                    continue

            # 새로운 광고가 추가되었는지 확인
            if len(ads_data) == previous_count:
                no_new_ads_count += 1
                if no_new_ads_count >= 3:
                    self.logger.info("더 이상 새로운 광고가 없습니다")
                    break
            else:
                no_new_ads_count = 0

            # 스크롤 다운하여 더 많은 광고 로드
            if collected < max_ads:
                has_new_content = self.scroll_down(self.scroll_pause)
                scroll_count += 1

                if not has_new_content and scroll_count >= 5:
                    self.logger.info("더 이상 스크롤할 콘텐츠가 없습니다")
                    break

                self.random_delay(1, 2)

        self.logger.info(f"Meta 광고 라이브러리 크롤링 완료: {len(ads_data)}개 광고 수집")
        return ads_data

    def _build_search_url(self, query: str, country: str = 'KR') -> str:
        """검색 URL 생성"""
        encoded_query = quote(query)
        url = (
            f"{self.BASE_URL}/"
            f"?active_status=active"
            f"&ad_type=all"
            f"&country={country}"
            f"&q={encoded_query}"
            f"&media_type=all"
        )
        return url

    def _find_ad_cards(self) -> List:
        """광고 카드 요소들 찾기"""
        selectors = self.selectors.get('ad_card', [])
        return self.safe_find_elements(self.driver, selectors)

    def extract_ad_info(self, ad_card) -> Optional[Dict]:
        """
        광고 카드에서 정보 추출

        Args:
            ad_card: 광고 카드 요소

        Returns:
            광고 정보 딕셔너리
        """
        try:
            info = {}

            # 광고주
            advertiser = self.safe_get_text(ad_card, self.selectors.get('advertiser', []))
            if not advertiser:
                # 광고주는 필수 정보
                return None
            info['advertiser'] = advertiser

            # 광고 링크
            ad_link = self.safe_get_attribute(ad_card, self.selectors.get('ad_link', []), 'href')
            info['ad_library_url'] = ad_link if ad_link else ''

            # 광고 ID 추출 (URL에서)
            ad_id = self._extract_ad_id(ad_link)
            info['ad_id'] = ad_id

            # 썸네일/비디오
            thumbnail_info = self._extract_media(ad_card)
            info.update(thumbnail_info)

            # 광고 텍스트
            ad_text = self.safe_get_text(ad_card, self.selectors.get('ad_text', []))
            info['ad_text'] = ad_text

            # 노출수 정보
            impression_text = self.safe_get_text(ad_card, self.selectors.get('impression', []))
            info['impression_text'] = impression_text

            # 게재 시작일
            date_text = self.safe_get_text(ad_card, self.selectors.get('start_date', []))
            info['start_date'] = date_text

            # 라이브 일수 계산
            days_live = self.calculate_days_live(date_text)
            info['days_live'] = days_live

            # 플랫폼 정보 (Facebook, Instagram 등)
            platform_text = self.safe_get_text(ad_card, self.selectors.get('platform', []))
            info['platforms'] = self._parse_platforms(platform_text)

            return info

        except Exception as e:
            self.logger.debug(f"광고 정보 추출 오류: {e}")
            return None

    def _extract_ad_id(self, ad_url: str) -> str:
        """광고 URL에서 ID 추출"""
        if not ad_url:
            return ""

        # URL 패턴: /ads/library/?id=123456789
        match = re.search(r'[?&]id=(\d+)', ad_url)
        if match:
            return match.group(1)

        return ""

    def _extract_media(self, ad_card) -> Dict:
        """미디어 정보 추출 (썸네일, 비디오)"""
        media_info = {
            'thumbnail_url': '',
            'video_url': '',
            'media_type': 'unknown'
        }

        thumbnail_selectors = self.selectors.get('thumbnail', [])
        media_elem = self.safe_find_element(ad_card, thumbnail_selectors)

        if media_elem:
            tag_name = media_elem.tag_name.lower()

            if tag_name == 'img':
                media_info['thumbnail_url'] = media_elem.get_attribute('src') or ''
                media_info['media_type'] = 'image'
            elif tag_name == 'video':
                media_info['video_url'] = media_elem.get_attribute('src') or ''
                media_info['thumbnail_url'] = media_elem.get_attribute('poster') or ''
                media_info['media_type'] = 'video'

        return media_info

    def _parse_platforms(self, platform_text: str) -> List[str]:
        """플랫폼 텍스트 파싱"""
        platforms = []

        if not platform_text:
            return platforms

        text_lower = platform_text.lower()

        if 'facebook' in text_lower or '페이스북' in text_lower:
            platforms.append('Facebook')
        if 'instagram' in text_lower or '인스타그램' in text_lower:
            platforms.append('Instagram')
        if 'messenger' in text_lower or '메신저' in text_lower:
            platforms.append('Messenger')
        if 'audience network' in text_lower or '오디언스 네트워크' in text_lower:
            platforms.append('Audience Network')

        return platforms

    def is_low_impression(self, ad_card) -> bool:
        """
        노출수 적음 광고 필터링

        Args:
            ad_card: 광고 카드 요소

        Returns:
            True: 제외해야 함 (노출수 적음)
            False: 수집 가능
        """
        impression_text = self.safe_get_text(ad_card, self.selectors.get('impression', []))

        if not impression_text:
            return False

        text_lower = impression_text.lower()

        # 필터 키워드 체크
        low_keywords = self.filter_keywords.get('low_impression', [])
        for keyword in low_keywords:
            if keyword.lower() in text_lower:
                return True

        return False

    def is_active_ad(self, ad_card) -> bool:
        """
        현재 라이브 중인 광고인지 확인

        Args:
            ad_card: 광고 카드 요소

        Returns:
            True: 현재 라이브 중
            False: 종료됨
        """
        # 게재 상태 텍스트 확인
        date_text = self.safe_get_text(ad_card, self.selectors.get('start_date', []))

        if not date_text:
            return True  # 정보 없으면 라이브로 간주

        text_lower = date_text.lower()

        # 비활성 키워드 체크
        inactive_keywords = self.filter_keywords.get('inactive_status', [])
        for keyword in inactive_keywords:
            if keyword.lower() in text_lower:
                return False

        # 활성 키워드 체크
        active_keywords = self.filter_keywords.get('active_status', [])
        for keyword in active_keywords:
            if keyword.lower() in text_lower:
                return True

        return True  # 기본값은 라이브

    def calculate_days_live(self, start_date_text: str) -> int:
        """
        게재 시작일로부터 현재까지 일수 계산

        Args:
            start_date_text: 날짜 텍스트

        Returns:
            라이브 일수 (정수)
        """
        if not start_date_text:
            return 0

        # 한국어 날짜 패턴
        korean_pattern = self.date_patterns.get('korean', r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일')
        match = re.search(korean_pattern, start_date_text)

        if match:
            year = int(match.group('year') if 'year' in match.groupdict() else match.group(1))
            month = int(match.group('month') if 'month' in match.groupdict() else match.group(2))
            day = int(match.group('day') if 'day' in match.groupdict() else match.group(3))

            try:
                start_date = datetime(year, month, day)
                days_live = (datetime.now() - start_date).days
                return max(0, days_live)
            except ValueError:
                return 0

        # 영어 날짜 패턴 시도
        english_pattern = self.date_patterns.get('english', r'(\w+)\s+(\d{1,2}),\s*(\d{4})')
        match = re.search(english_pattern, start_date_text)

        if match:
            try:
                month_str = match.group('month') if 'month' in match.groupdict() else match.group(1)
                day = int(match.group('day') if 'day' in match.groupdict() else match.group(2))
                year = int(match.group('year') if 'year' in match.groupdict() else match.group(3))

                # 월 이름을 숫자로 변환
                month_map = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month = month_map.get(month_str.lower(), 1)

                start_date = datetime(year, month, day)
                days_live = (datetime.now() - start_date).days
                return max(0, days_live)
            except (ValueError, KeyError):
                return 0

        return 0
