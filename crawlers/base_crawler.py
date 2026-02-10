import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class BaseCrawler(ABC):
    """모든 크롤러의 기본 클래스"""

    def __init__(self, config: Dict):
        """
        크롤러 초기화

        Args:
            config: 크롤링 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.driver: Optional[webdriver.Chrome] = None

        # 설정값 불러오기
        self.crawl_delay_min = config.get('crawl_delay_min', 3)
        self.crawl_delay_max = config.get('crawl_delay_max', 7)
        self.max_retry = config.get('max_retry', 3)
        self.max_products = config.get('max_products_per_keyword', 100)

    def setup_driver(self) -> webdriver.Chrome:
        """Chrome 드라이버 설정"""
        chrome_options = Options()

        # 헤드리스 모드 (필요시 주석 해제)
        # chrome_options.add_argument('--headless')

        # 기본 옵션
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # User-Agent 설정
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 드라이버 생성
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # WebDriver 탐지 방지
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        self.logger.info("Chrome 드라이버 설정 완료")
        return driver

    def random_delay(self):
        """랜덤 대기 시간"""
        delay = random.uniform(self.crawl_delay_min, self.crawl_delay_max)
        self.logger.debug(f"{delay:.2f}초 대기 중...")
        time.sleep(delay)

    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """요소가 로드될 때까지 대기"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"요소를 찾을 수 없음: {value}")
            return None

    def scroll_down(self, pause_time: float = 1.0):
        """페이지 스크롤 다운"""
        scroll_pause_time = pause_time
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # 스크롤 다운
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            # 새 높이 계산
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def safe_get_text(self, element, selector: str, by: By = By.CSS_SELECTOR) -> str:
        """안전하게 텍스트 추출"""
        try:
            return element.find_element(by, selector).text.strip()
        except (NoSuchElementException, AttributeError):
            return ""

    def safe_get_attribute(self, element, selector: str, attribute: str, by: By = By.CSS_SELECTOR) -> str:
        """안전하게 속성 추출"""
        try:
            return element.find_element(by, selector).get_attribute(attribute)
        except (NoSuchElementException, AttributeError):
            return ""

    @abstractmethod
    def crawl_products(self, keyword: str) -> List[Dict]:
        """
        제품 크롤링 (추상 메서드)

        Args:
            keyword: 검색 키워드

        Returns:
            제품 정보 리스트
        """
        pass

    @abstractmethod
    def parse_product_info(self, element) -> Dict:
        """
        제품 정보 파싱 (추상 메서드)

        Args:
            element: 제품 요소

        Returns:
            제품 정보 딕셔너리
        """
        pass

    def start(self):
        """드라이버 시작"""
        if not self.driver:
            self.driver = self.setup_driver()
            self.logger.info("크롤러 시작")

    def stop(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("크롤러 종료")

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop()
