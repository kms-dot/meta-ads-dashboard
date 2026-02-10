import re
import logging
from typing import List, Set, Dict
from collections import Counter


class KeywordCleaner:
    """제품명에서 키워드를 추출하고 정제하는 클래스"""

    def __init__(self, config: Dict):
        """
        초기화

        Args:
            config: 카테고리 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 제거할 불용어
        self.stopwords = self._load_stopwords()

        # 제품 타입 키워드
        self.product_types = set(config.get('product_types', []))

        # 기능 키워드
        self.function_keywords = set(config.get('function_keywords', []))

    def _load_stopwords(self) -> Set[str]:
        """불용어 목록 로드"""
        stopwords = {
            # 일반 불용어
            '공식', '정품', '빠른배송', '무료배송', '당일배송', '오늘출발',
            '국내배송', '해외직구', '즉시발송', '특가', '세일', '할인',
            '이벤트', '기획', '증정', '사은품', '덤', '추가구성',

            # 용량/수량 관련
            'ml', 'g', 'mg', 'l', 'kg', '개입', '매입', '입', '개',
            '미니', '대용량', '소용량', '정량', '증량',

            # 기타
            '새제품', '리뉴얼', '신상', '신제품', '출시', 'new', 'NEW',
            '한정', '한정판', '스페셜', 'set', 'SET', '세트',
            '본품', '리필', '파우치', '증정품',

            # 브래킷 관련
            '[', ']', '(', ')', '{', '}', '<', '>',

            # 기호
            '+', '/', '|', '~', '*', '#', '@', '!', '?',
        }
        return stopwords

    def clean_product_name(self, product_name: str) -> str:
        """
        제품명 정제

        Args:
            product_name: 원본 제품명

        Returns:
            정제된 제품명
        """
        if not product_name:
            return ""

        # 소문자 변환
        cleaned = product_name.lower()

        # 특수문자 제거 (일부 유지)
        cleaned = re.sub(r'[^\w\s가-힣a-zA-Z0-9+\-/]', ' ', cleaned)

        # 숫자+단위 패턴 제거 (예: 100ml, 50g)
        cleaned = re.sub(r'\d+\s*(ml|g|mg|l|kg|개|입|매)', ' ', cleaned)

        # 여러 공백을 하나로
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned.strip()

    def extract_keywords(self, product_name: str, min_length: int = 2) -> List[str]:
        """
        제품명에서 키워드 추출

        Args:
            product_name: 제품명
            min_length: 최소 키워드 길이

        Returns:
            키워드 리스트
        """
        # 제품명 정제
        cleaned_name = self.clean_product_name(product_name)

        # 공백으로 분리
        words = cleaned_name.split()

        # 키워드 필터링
        keywords = []
        for word in words:
            # 길이 체크
            if len(word) < min_length:
                continue

            # 불용어 체크
            if word in self.stopwords:
                continue

            # 숫자만 있는 경우 제외
            if word.isdigit():
                continue

            keywords.append(word)

        return keywords

    def extract_product_types(self, product_name: str) -> List[str]:
        """
        제품 타입 추출

        Args:
            product_name: 제품명

        Returns:
            제품 타입 리스트
        """
        cleaned_name = self.clean_product_name(product_name)
        found_types = []

        for product_type in self.product_types:
            if product_type.lower() in cleaned_name:
                found_types.append(product_type)

        return found_types

    def extract_functions(self, product_name: str) -> List[str]:
        """
        기능 키워드 추출

        Args:
            product_name: 제품명

        Returns:
            기능 키워드 리스트
        """
        cleaned_name = self.clean_product_name(product_name)
        found_functions = []

        for function_keyword in self.function_keywords:
            if function_keyword.lower() in cleaned_name:
                found_functions.append(function_keyword)

        return found_functions

    def get_top_keywords(self, products: List[Dict], top_n: int = 50) -> List[tuple]:
        """
        제품 리스트에서 상위 키워드 추출

        Args:
            products: 제품 정보 리스트
            top_n: 상위 n개 키워드

        Returns:
            (키워드, 빈도) 튜플 리스트
        """
        all_keywords = []

        for product in products:
            product_name = product.get('name', '')
            keywords = self.extract_keywords(product_name)
            all_keywords.extend(keywords)

        # 빈도 계산
        keyword_counter = Counter(all_keywords)

        # 상위 n개 반환
        top_keywords = keyword_counter.most_common(top_n)

        self.logger.info(f"상위 {top_n}개 키워드 추출 완료: {len(top_keywords)}개")

        return top_keywords

    def filter_by_keywords(self, products: List[Dict], keywords: List[str]) -> List[Dict]:
        """
        특정 키워드를 포함하는 제품만 필터링

        Args:
            products: 제품 정보 리스트
            keywords: 필터링할 키워드 리스트

        Returns:
            필터링된 제품 리스트
        """
        filtered_products = []

        for product in products:
            product_name = product.get('name', '').lower()

            # 키워드 중 하나라도 포함하면 추가
            if any(keyword.lower() in product_name for keyword in keywords):
                filtered_products.append(product)

        self.logger.info(f"키워드 필터링 완료: {len(filtered_products)}/{len(products)}개 제품")

        return filtered_products

    def generate_search_keywords(self, category_config: Dict, max_keywords: int = 5) -> List[str]:
        """
        카테고리 설정을 기반으로 검색 키워드 생성

        Args:
            category_config: 카테고리 설정
            max_keywords: 최대 키워드 수

        Returns:
            검색 키워드 리스트
        """
        search_keywords = []

        product_types = category_config.get('product_types', [])
        function_keywords = category_config.get('function_keywords', [])

        # 제품 타입 추가
        search_keywords.extend(product_types[:max_keywords])

        # 기능 + 제품 타입 조합
        if function_keywords and product_types:
            for func in function_keywords[:2]:
                for ptype in product_types[:2]:
                    combined = f"{func} {ptype}"
                    search_keywords.append(combined)
                    if len(search_keywords) >= max_keywords:
                        break
                if len(search_keywords) >= max_keywords:
                    break

        # 중복 제거
        search_keywords = list(dict.fromkeys(search_keywords))

        self.logger.info(f"검색 키워드 생성 완료: {len(search_keywords)}개")

        return search_keywords[:max_keywords]

    def normalize_brand_name(self, brand_name: str) -> str:
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
        normalized = brand_name.lower()

        # 특수문자 제거
        normalized = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', '', normalized)

        # 공백 제거
        normalized = normalized.replace(' ', '')

        return normalized.strip()
