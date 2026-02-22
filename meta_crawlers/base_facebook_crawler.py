import time
import random
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class BaseFacebookCrawler(ABC):
    """Meta/Facebook 크롤러의 기본 클래스"""

    def __init__(self, config: Dict):
        """
        크롤러 초기화

        Args:
            config: 크롤링 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.driver: Optional[webdriver.Chrome] = None

        # 셀렉터 설정 로드
        self.selectors = self._load_selectors()

        # 설정값
        self.max_scrolls = config.get('max_scrolls', 50)
        self.scroll_pause = config.get('scroll_pause', 2)
        self.max_retries = config.get('max_retries', 3)
        self.page_load_timeout = config.get('page_load_timeout', 10)

    def _load_selectors(self) -> Dict:
        """셀렉터 설정 파일 로드"""
        try:
            with open('config/meta_selectors.json', 'r', encoding='utf-8') as f:
                selector_config = json.load(f)
                return selector_config.get('selectors', {})
        except FileNotFoundError:
            self.logger.warning("meta_selectors.json 파일을 찾을 수 없습니다. 기본 셀렉터 사용")
            return self._get_default_selectors()

    def _get_default_selectors(self) -> Dict:
        """기본 셀렉터 반환"""
        return {
            'ad_card': ["div[class*='x1n2onr6']", "div[data-testid='ad-card']"],
            'advertiser': ["span[class*='advertiser']", "a[href*='/ads/library/?active_status']"],
            'thumbnail': ["img[class*='img']", "video[class*='video']"],
            'impression': ["div[class*='impression']", "span[class*='impression']"],
            'start_date': ["div[class*='date']", "span[class*='date']"],
            'ad_link': ["a[href*='/ads/library/?id=']", "a[data-testid='ad-link']"],
        }

    def setup_driver(self) -> webdriver.Chrome:
        """Chrome 드라이버 설정"""
        chrome_options = Options()

        # 기본 옵션
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 언어 설정 (한국어)
        chrome_options.add_argument('--lang=ko-KR')
        chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'ko-KR,ko'})

        # User-Agent 설정
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 창 크기 설정 (광고 썸네일 로드를 위해 충분히 크게)
        chrome_options.add_argument('--window-size=1920,1080')

        # 드라이버 생성
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # WebDriver 탐지 방지
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            '''
        })

        # 페이지 로드 타임아웃 설정
        driver.set_page_load_timeout(self.page_load_timeout)

        self.logger.info("Chrome 드라이버 설정 완료")
        return driver

    def safe_find_element(self, parent_element, selectors: List[str], by_type: str = 'auto') -> Optional[Any]:
        """
        여러 셀렉터를 순차적으로 시도하여 요소 찾기

        Args:
            parent_element: 부모 요소 (driver 또는 WebElement)
            selectors: 시도할 셀렉터 리스트
            by_type: 'auto', 'css', 'xpath' 중 하나

        Returns:
            찾은 요소 또는 None
        """
        for selector in selectors:
            try:
                # XPath 자동 감지
                if by_type == 'auto':
                    # XPath 패턴: //, .// 또는 (//로 시작
                    if selector.startswith('//') or selector.startswith('.//') or selector.startswith('(//'):
                        by = By.XPATH
                    else:
                        by = By.CSS_SELECTOR
                elif by_type == 'xpath':
                    by = By.XPATH
                else:
                    by = By.CSS_SELECTOR

                # 요소 찾기
                elem = parent_element.find_element(by, selector)

                # 요소가 표시되는지 확인
                if elem and elem.is_displayed():
                    return elem

            except (NoSuchElementException, StaleElementReferenceException):
                continue
            except Exception as e:
                self.logger.debug(f"셀렉터 '{selector}' 시도 중 오류: {e}")
                continue

        return None

    def safe_find_elements(self, parent_element, selectors: List[str], by_type: str = 'auto') -> List[Any]:
        """
        여러 셀렉터를 순차적으로 시도하여 요소들 찾기

        Args:
            parent_element: 부모 요소
            selectors: 시도할 셀렉터 리스트
            by_type: 'auto', 'css', 'xpath' 중 하나

        Returns:
            찾은 요소 리스트
        """
        for selector in selectors:
            try:
                # XPath 자동 감지
                if by_type == 'auto':
                    # XPath 패턴: //, .// 또는 (//로 시작
                    if selector.startswith('//') or selector.startswith('.//') or selector.startswith('(//'):
                        by = By.XPATH
                    else:
                        by = By.CSS_SELECTOR
                elif by_type == 'xpath':
                    by = By.XPATH
                else:
                    by = By.CSS_SELECTOR

                # 요소들 찾기
                elems = parent_element.find_elements(by, selector)

                if elems:
                    return elems

            except Exception as e:
                self.logger.debug(f"셀렉터 '{selector}' 시도 중 오류: {e}")
                continue

        return []

    def safe_get_text(self, element, selectors: List[str]) -> str:
        """안전하게 텍스트 추출"""
        found_elem = self.safe_find_element(element, selectors)
        if found_elem:
            try:
                return found_elem.text.strip()
            except StaleElementReferenceException:
                return ""
        return ""

    def safe_get_attribute(self, element, selectors: List[str], attribute: str) -> str:
        """안전하게 속성 추출"""
        found_elem = self.safe_find_element(element, selectors)
        if found_elem:
            try:
                return found_elem.get_attribute(attribute) or ""
            except StaleElementReferenceException:
                return ""
        return ""

    def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """랜덤 대기 시간"""
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"{delay:.2f}초 대기 중...")
        time.sleep(delay)

    def scroll_down(self, pause_time: float = None):
        """페이지 스크롤 다운"""
        if pause_time is None:
            pause_time = self.scroll_pause

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        # 스크롤 다운
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)

        # 새 높이 확인
        new_height = self.driver.execute_script("return document.body.scrollHeight")

        return new_height != last_height  # 새 콘텐츠가 로드되었는지 여부

    def scroll_to_element(self, element):
        """특정 요소로 스크롤"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
        except Exception as e:
            self.logger.debug(f"요소로 스크롤 실패: {e}")

    def wait_for_element(self, selectors: List[str], timeout: int = 10) -> Optional[Any]:
        """요소가 로드될 때까지 대기"""
        for selector in selectors:
            try:
                if selector.startswith('//'):
                    by = By.XPATH
                else:
                    by = By.CSS_SELECTOR

                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                if element:
                    return element
            except TimeoutException:
                continue

        self.logger.warning(f"요소를 찾을 수 없음: {selectors}")
        return None

    def execute_with_retry(self, func, max_retries: int = None, *args, **kwargs):
        """재시도 로직을 포함한 함수 실행"""
        if max_retries is None:
            max_retries = self.max_retries

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"시도 {attempt + 1}/{max_retries} 실패: {e}")
                if attempt < max_retries - 1:
                    self.random_delay(2, 5)
                else:
                    raise

    @abstractmethod
    def crawl(self, *args, **kwargs) -> List[Dict]:
        """크롤링 메서드 (추상 메서드)"""
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
