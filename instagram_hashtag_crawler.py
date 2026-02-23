"""
Instagram 해시태그 크롤러 (바이럴 컨텐츠 수집)
==============================================
실행: python instagram_hashtag_crawler.py [--category 뷰티디바이스] [--dry-run]

수집 흐름
---------
  카테고리 → priority_hashtags (top N) → 탐색 페이지 접속
  → Recent 탭 → 릴스/비디오 필터 → 포스트 상세 수집
  → 바이럴 점수 계산 → meta_output/viral_posts.json 저장

바이럴 점수 공식
--------------
  viral_score = views×1 + likes×10 + comments×50 + shares×100
  (게시 날짜는 화면 표기용 "N일 전"에만 사용, 점수에 미적용)

주의
----
- 로그인 없이 공개 해시태그에 직접 접근 (비로그인 모드 전용)
- 일부 수치(좋아요 수 등)는 비로그인 시 제한될 수 있음
- Instagram 로그인 팝업 자동 닫기 처리 포함
- User-Agent 로테이션 + 딜레이로 차단 방지
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# ─────────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────────
BASE_DIR         = Path(__file__).parent
CONFIG_FILE      = BASE_DIR / "config" / "hashtag_keywords.json"
OUTPUT_DIR       = BASE_DIR / "meta_output"
VIRAL_POSTS_FILE = OUTPUT_DIR / "viral_posts.json"

# ─────────────────────────────────────────────────
# 환경 변수
# ─────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─────────────────────────────────────────────────
# 로깅
# ─────────────────────────────────────────────────
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(
            OUTPUT_DIR / f"hashtag_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ig_hashtag")

# ─────────────────────────────────────────────────
# User-Agent 풀 (로테이션)
# ─────────────────────────────────────────────────
_USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
     "AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/121.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
     "AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/120.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (X11; Linux x86_64) "
     "AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/119.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
     "Gecko/20100101 Firefox/122.0"),
]

# ─────────────────────────────────────────────────
# 바이럴 점수
# ─────────────────────────────────────────────────
def calc_viral_score(views: int, likes: int,
                     comments: int, shares: int) -> float:
    """viral_score = views×1 + likes×10 + comments×50 + shares×100
    ※ 게시 날짜는 점수 계산에 미사용 (화면 표기용만)
    """
    return float(views * 1 + likes * 10 + comments * 50 + shares * 100)


def days_ago_label(post_date_str: str) -> str:
    """'YYYY-MM-DD' → 'N일 전' 문자열"""
    try:
        d = (date.today() - datetime.strptime(post_date_str, "%Y-%m-%d").date()).days
        if d == 0:  return "오늘"
        if d == 1:  return "1일 전"
        return f"{d}일 전"
    except Exception:
        return "날짜 불명"


# ─────────────────────────────────────────────────
# 숫자 파싱 ("1.2만" → 12000)
# ─────────────────────────────────────────────────
def parse_metric(text: str) -> int:
    if not text:
        return 0
    text = text.strip().replace(",", "").replace(" ", "")
    try:
        if "만" in text:
            return int(float(text.replace("만", "")) * 10_000)
        if "천" in text:
            return int(float(text.replace("천", "")) * 1_000)
        if text.upper().endswith("K"):
            return int(float(text[:-1]) * 1_000)
        if text.upper().endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        return int(re.sub(r"[^\d]", "", text) or 0)
    except ValueError:
        return 0


# ─────────────────────────────────────────────────
# Selenium 드라이버 빌드
# ─────────────────────────────────────────────────
def build_driver(headless: bool = True) -> webdriver.Chrome:
    ua = random.choice(_USER_AGENTS)
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument(f"user-agent={ua}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--lang=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts,
    )
    # webdriver 속성 숨기기
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": (
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "window.chrome={runtime:{}};"
        )
    })
    driver.set_page_load_timeout(30)
    return driver


# ─────────────────────────────────────────────────
# 팝업/배너 닫기
# ─────────────────────────────────────────────────
def dismiss_popups(driver: webdriver.Chrome):
    """로그인 유도·쿠키 배너 닫기 (비로그인 모드 최적화)"""
    # CSS 셀렉터 기반 닫기 버튼
    css_selectors = [
        "button._a9--._a9_1",                    # 로그인 모달 닫기
        "button[type='button'][class*='close']",
        "div[role='dialog'] button:last-of-type",
    ]
    for sel in css_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.6)
        except Exception:
            continue

    # XPath 기반 (한국어/영어 버튼 텍스트)
    xpath_buttons = [
        "//div[@role='dialog']//button[contains(text(),'나중에')]",
        "//div[@role='dialog']//button[contains(text(),'나중에 하기')]",
        "//div[@role='dialog']//button[contains(text(),'Not Now')]",
        "//button[contains(text(),'로그인 없이 계속')]",
        "//button[contains(text(),'Continue without logging in')]",
        "//button[contains(text(),'필수만 허용')]",
        "//button[contains(text(),'모두 허용')]",
        "//button[contains(text(),'동의')]",
        "//div[contains(@class,'_aa_u')]//button",  # 앱 다운로드 배너
    ]
    for xpath in xpath_buttons:
        try:
            el = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.6)
        except Exception:
            continue


# ─────────────────────────────────────────────────
# 해시태그 탐색 페이지 접속 + Recent 탭 클릭
# ─────────────────────────────────────────────────
def open_hashtag_page(driver: webdriver.Chrome,
                      hashtag: str) -> bool:
    """https://www.instagram.com/explore/tags/{hashtag}/ 접속 후 최근 탭 선택
    비로그인 모드: 로그인 리다이렉트 감지 시 팝업 닫고 재접속
    """
    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
    try:
        driver.get(url)
        time.sleep(random.uniform(2.0, 3.0))

        # ── 로그인 페이지 리다이렉트 처리 ──
        if "accounts/login" in driver.current_url:
            logger.debug(f"[{hashtag}] 로그인 리다이렉트 감지 → 팝업 닫고 재접속")
            dismiss_popups(driver)
            time.sleep(1.0)
            driver.get(url)
            time.sleep(random.uniform(2.5, 3.5))

        # ── 로그인 모달/배너 닫기 ──
        dismiss_popups(driver)
        time.sleep(0.8)

        # ── 페이지 로드 확인 ──
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        except TimeoutException:
            # article 태그 없어도 main 영역 존재하면 진행
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[role='main']")
                    )
                )
                logger.debug(f"[{hashtag}] article 없음 → main 영역으로 진행")
            except TimeoutException:
                logger.warning(f"[{hashtag}] 페이지 로드 타임아웃")
                return False

        time.sleep(random.uniform(1.5, 2.5))

        # ── 최근 탭 클릭 ──
        _click_recent_tab(driver)
        time.sleep(random.uniform(1.0, 1.8))
        return True

    except TimeoutException:
        logger.warning(f"[{hashtag}] 페이지 로드 타임아웃")
        return False
    except Exception as e:
        logger.warning(f"[{hashtag}] 접속 오류: {e}")
        return False


def _click_recent_tab(driver: webdriver.Chrome):
    """최근(Recent) 탭 선택"""
    candidates = [
        "//span[contains(text(),'최근')]",
        "//span[contains(text(),'Recent')]",
        "//div[@role='tab'][contains(.,'최근')]",
        "//div[@role='tab'][contains(.,'Recent')]",
    ]
    for xpath in candidates:
        try:
            el = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", el)
            logger.debug("최근 탭 클릭 성공")
            return
        except NoSuchElementException:
            continue
    logger.debug("최근 탭 버튼을 찾지 못함 (기본 탭 사용)")


# ─────────────────────────────────────────────────
# 해시태그 페이지에서 포스트 링크 수집
# ─────────────────────────────────────────────────
def collect_post_links(driver: webdriver.Chrome,
                       max_posts: int = 20) -> List[str]:
    """페이지에서 최대 max_posts 개의 포스트 URL 수집 (릴스/비디오 우선)"""
    post_urls: List[str] = []
    scroll_attempts = 0
    max_scroll = 8

    while len(post_urls) < max_posts and scroll_attempts < max_scroll:
        # 포스트 링크 요소 탐색
        try:
            anchors = driver.find_elements(
                By.CSS_SELECTOR,
                "article a[href*='/p/'], article a[href*='/reel/']"
            )
        except Exception:
            anchors = []

        for a in anchors:
            try:
                href = a.get_attribute("href")
                if href and href not in post_urls:
                    # 릴스 우선 (비디오 아이콘 감지)
                    try:
                        a.find_element(By.CSS_SELECTOR,
                                       "svg[aria-label*='릴스'], svg[aria-label*='Reel'], "
                                       "svg[aria-label*='Video'], span[class*='video']")
                        post_urls.insert(0, href)        # 릴스 → 앞에 삽입
                    except NoSuchElementException:
                        post_urls.append(href)           # 일반 포스트 → 뒤에 추가
            except StaleElementReferenceException:
                continue

        if len(post_urls) >= max_posts:
            break

        # 스크롤 다운
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(random.uniform(1.2, 2.0))
        scroll_attempts += 1

    unique_urls = list(dict.fromkeys(post_urls))[:max_posts]
    logger.debug(f"  수집된 포스트 링크: {len(unique_urls)}개")
    return unique_urls


# ─────────────────────────────────────────────────
# 단일 포스트 상세 데이터 스크래핑
# ─────────────────────────────────────────────────
def scrape_post_detail(driver: webdriver.Chrome,
                       post_url: str,
                       retries: int = 3) -> Optional[Dict]:
    """포스트 1건의 상세 데이터 수집"""
    for attempt in range(1, retries + 1):
        try:
            driver.get(post_url)
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            dismiss_popups(driver)
            time.sleep(random.uniform(1.5, 2.5))

            rec: Dict = {
                "instagram_url":      post_url,
                "thumbnail_url":      "",
                "instagram_views":    0,
                "instagram_likes":    0,
                "instagram_comments": 0,
                "instagram_shares":   0,
                "post_date":          "",
                "caption_text":       "",
                "is_reel":            False,
            }

            # ── 썸네일 ──
            try:
                img = driver.find_element(
                    By.CSS_SELECTOR,
                    "article img[src*='cdninstagram'], article img[src*='fbcdn']"
                )
                rec["thumbnail_url"] = img.get_attribute("src")
            except NoSuchElementException:
                pass

            # ── 릴스 여부 ──
            try:
                driver.find_element(
                    By.XPATH,
                    "//*[contains(@aria-label,'릴스') or contains(@aria-label,'Reel')]"
                )
                rec["is_reel"] = True
            except NoSuchElementException:
                pass

            # ── 조회수 (릴스/비디오) ──
            try:
                view_el = driver.find_element(
                    By.XPATH,
                    "//*[contains(text(),'회') or contains(text(),'views') or "
                    "contains(@aria-label,'재생') or contains(@aria-label,'view')]"
                )
                rec["instagram_views"] = parse_metric(
                    re.sub(r"[^\d만천KkMm.,]", "", view_el.text)
                )
            except NoSuchElementException:
                pass

            # ── 좋아요 수 ──
            _extract_likes(driver, rec)

            # ── 댓글 수 ──
            _extract_comments(driver, rec)

            # ── 공유 수 (가능 시) ──
            # Instagram 은 공유 수를 공개하지 않으므로 0으로 설정
            # (향후 API 변경 시 업데이트)
            rec["instagram_shares"] = 0

            # ── 게시일 ──
            try:
                time_el = driver.find_element(
                    By.CSS_SELECTOR, "article time[datetime]"
                )
                dt_raw = time_el.get_attribute("datetime")   # ISO 8601
                rec["post_date"] = dt_raw[:10]               # YYYY-MM-DD
            except NoSuchElementException:
                pass

            # ── 캡션 텍스트 ──
            try:
                cap_el = driver.find_element(
                    By.CSS_SELECTOR,
                    "article div[class*='_a9zs'] h1, "
                    "article span[class*='_aacl']"
                )
                rec["caption_text"] = cap_el.text.strip()
            except NoSuchElementException:
                pass

            return rec

        except TimeoutException:
            logger.warning(f"  타임아웃 (시도 {attempt}/{retries}): {post_url}")
        except WebDriverException as e:
            logger.warning(f"  WebDriver 오류 (시도 {attempt}/{retries}): {e}")

        if attempt < retries:
            time.sleep(random.uniform(3.0, 5.0))

    return None


# ─────────────────────────────────────────────────
# 좋아요·댓글 추출 헬퍼
# ─────────────────────────────────────────────────
def _extract_likes(driver: webdriver.Chrome, rec: Dict):
    selectors = [
        # 비로그인 환경 셀렉터
        "section span[class*='x193iq5w']",
        "a[href*='liked_by'] span",
        "button[class*='like'] span",
        "//span[contains(@class,'_aacl')][contains(text(),'좋아요') or "
        "contains(text(),'like')]//preceding-sibling::span",
        "//button[@type='button']//span[contains(text(),'개')]",
    ]
    for sel in selectors:
        try:
            if sel.startswith("//"):
                el = driver.find_element(By.XPATH, sel)
            else:
                el = driver.find_element(By.CSS_SELECTOR, sel)
            val = parse_metric(re.sub(r"[^\d만천KkMm.,]", "", el.text))
            if val > 0:
                rec["instagram_likes"] = val
                return
        except Exception:
            continue


def _extract_comments(driver: webdriver.Chrome, rec: Dict):
    # 댓글 카운트 텍스트 탐색
    try:
        els = driver.find_elements(
            By.XPATH,
            "//span[contains(text(),'댓글') or contains(text(),'comment')]"
            "/preceding-sibling::span | "
            "//a[contains(@href,'/comments')]//span"
        )
        for el in els:
            val = parse_metric(re.sub(r"[^\d만천KkMm.,]", "", el.text))
            if val > 0:
                rec["instagram_comments"] = val
                return
    except Exception:
        pass
    # 폴백: 댓글 DOM 개수
    try:
        items = driver.find_elements(
            By.CSS_SELECTOR,
            "ul li[class*='comment'], div[class*='_a9ym']"
        )
        rec["instagram_comments"] = len(items)
    except Exception:
        pass


# ─────────────────────────────────────────────────
# 해시태그 1개 크롤
# ─────────────────────────────────────────────────
def crawl_hashtag(driver: webdriver.Chrome,
                  hashtag: str,
                  category: str,
                  max_posts: int = 20) -> List[Dict]:
    """단일 해시태그 크롤링 → 포스트 리스트 반환"""
    logger.info(f"  [{category}] #{hashtag} 크롤 시작")

    if not open_hashtag_page(driver, hashtag):
        return []

    post_urls = collect_post_links(driver, max_posts)
    if not post_urls:
        logger.warning(f"  [{hashtag}] 수집된 포스트 없음")
        return []

    posts: List[Dict] = []
    for idx, url in enumerate(post_urls, 1):
        logger.debug(f"    포스트 {idx}/{len(post_urls)}: {url}")
        detail = scrape_post_detail(driver, url)

        if detail:
            # 바이럴 점수 계산
            detail["viral_score"] = calc_viral_score(
                detail["instagram_views"],
                detail["instagram_likes"],
                detail["instagram_comments"],
                detail["instagram_shares"],
            )
            detail["hashtag"]      = hashtag
            detail["category"]     = category
            detail["source"]       = "instagram_hashtag"
            detail["collected_at"] = datetime.now().isoformat()
            posts.append(detail)

        # 요청 간 딜레이 (IP 차단 방지)
        time.sleep(random.uniform(2.0, 3.5))

    logger.info(f"  [{hashtag}] 완료: {len(posts)}개 포스트 수집")
    return posts


# ─────────────────────────────────────────────────
# viral_posts.json 로드 / 저장
# ─────────────────────────────────────────────────
def load_existing_posts() -> Dict[str, Dict]:
    """기존 viral_posts.json 로드 → {instagram_url: post_dict}"""
    if not VIRAL_POSTS_FILE.exists():
        return {}
    try:
        with open(VIRAL_POSTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {p["instagram_url"]: p for p in raw.get("posts", [])}
    except Exception as e:
        logger.warning(f"기존 데이터 로드 실패: {e}")
        return {}


def save_posts(posts_dict: Dict[str, Dict]):
    """viral_posts.json 저장"""
    posts_list = sorted(
        posts_dict.values(),
        key=lambda x: x.get("viral_score", 0),
        reverse=True,
    )
    payload = {
        "last_updated": datetime.now().isoformat(),
        "total_posts":  len(posts_list),
        "categories":   list({p.get("category", "") for p in posts_list}),
        "posts":        posts_list,
    }
    with open(VIRAL_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(f"저장 완료: {VIRAL_POSTS_FILE}  (총 {len(posts_list)}건)")


# ─────────────────────────────────────────────────
# 전체 카테고리 오케스트레이션
# ─────────────────────────────────────────────────
def run_all_categories(driver: webdriver.Chrome,
                       config: Dict,
                       target_category: Optional[str] = None,
                       dry_run: bool = False) -> Dict[str, Dict]:
    """모든 (또는 지정) 카테고리를 순회하며 크롤"""
    settings   = config.get("crawl_settings", {})
    top_n      = settings.get("top_hashtags_per_category", 10)
    max_posts  = settings.get("max_posts_per_hashtag", 20)
    categories = config.get("categories", {})

    existing   = load_existing_posts()
    logger.info(f"기존 저장 데이터: {len(existing)}건")

    all_posts  = dict(existing)   # 기존 데이터 보존 + 신규 병합

    for cat_name, cat_cfg in categories.items():
        if target_category and cat_name != target_category:
            continue

        hashtags = cat_cfg.get("priority_hashtags",
                               cat_cfg.get("hashtags", []))[:top_n]

        logger.info(f"[{cat_name}] 해시태그 {len(hashtags)}개 크롤 시작")

        for tag in hashtags:
            if dry_run:
                logger.info(f"  [DRY-RUN] #{tag} 스킵")
                continue

            new_posts = crawl_hashtag(driver, tag, cat_name, max_posts)

            for p in new_posts:
                url = p["instagram_url"]
                # 동일 URL 이면 바이럴 점수가 높은 것 유지
                if url not in all_posts or \
                   p["viral_score"] > all_posts[url].get("viral_score", 0):
                    all_posts[url] = p

            # 카테고리 내 해시태그 간 딜레이
            time.sleep(random.uniform(2.5, 4.0))

        logger.info(f"[{cat_name}] 완료 (누적 {len(all_posts)}건)")

        # 카테고리 완료마다 중간 저장
        save_posts(all_posts)

    return all_posts


# ─────────────────────────────────────────────────
# 메인 진입점
# ─────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Instagram 해시태그 바이럴 컨텐츠 크롤러"
    )
    parser.add_argument(
        "--category", type=str, default=None,
        help="특정 카테고리만 크롤 (예: 뷰티디바이스). 기본값: 전체",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 크롤 없이 설정 확인만",
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="브라우저 창 표시 (디버깅용)",
    )
    return parser.parse_args()


def main():
    args    = parse_args()
    headless = not args.no_headless

    logger.info("=" * 60)
    logger.info("Instagram 해시태그 크롤러 시작")
    logger.info(f"  카테고리  : {args.category or '전체'}")
    logger.info(f"  dry-run   : {args.dry_run}")
    logger.info(f"  headless  : {headless}")
    logger.info("=" * 60)

    # 설정 파일 로드
    if not CONFIG_FILE.exists():
        logger.error(f"설정 파일 없음: {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 설정 요약 출력
    cats = config.get("categories", {})
    s    = config.get("crawl_settings", {})
    logger.info(
        f"설정 로드: {len(cats)}개 카테고리, "
        f"해시태그 top {s.get('top_hashtags_per_category')}개, "
        f"포스트 최대 {s.get('max_posts_per_hashtag')}개"
    )

    if args.dry_run:
        logger.info("[DRY-RUN] 드라이버 미실행")
        for cat, cfg in cats.items():
            tags = cfg.get("priority_hashtags", cfg.get("hashtags", []))
            logger.info(f"  {cat}: {tags[:s.get('top_hashtags_per_category',10)]}")
        return

    # Selenium 드라이버 시작 (비로그인 모드)
    logger.info("비로그인 모드로 크롤러 시작")
    driver = build_driver(headless=headless)

    try:
        all_posts = run_all_categories(
            driver,
            config,
            target_category=args.category,
            dry_run=args.dry_run,
        )
        save_posts(all_posts)

        total = len(all_posts)
        has_viral = sum(1 for p in all_posts.values() if p.get("viral_score", 0) > 0)
        logger.info("=" * 60)
        logger.info(f"크롤 완료 — 총 {total}건 (바이럴 점수 있음: {has_viral}건)")
        logger.info(f"결과 파일: {VIRAL_POSTS_FILE}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("사용자 중단 — 현재까지 결과 저장 중...")
        save_posts(load_existing_posts())

    finally:
        driver.quit()
        logger.info("드라이버 종료")


if __name__ == "__main__":
    main()
