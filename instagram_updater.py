"""
Instagram 성과 데이터 수집 + 바이럴 점수 계산기
================================================
실행: python instagram_updater.py

역할
----
1. meta_output/ 의 최신 광고 JSON에서 instagram_url 추출
2. Selenium 으로 Instagram 포스트/릴스 방문
3. 조회수·좋아요·댓글·캡션·게시일 스크래핑
4. CTA 감지 (detect_cta) + 바이럴 점수 계산
5. meta_output/instagram_data.json 저장 (기존 데이터 보존, 신규 병합)

주의
----
- Instagram 은 로그인 없이 접근이 제한될 수 있음.
  .env 에 IG_USERNAME / IG_PASSWORD 설정 시 자동 로그인.
- 수집 실패 항목은 스킵하고 계속 진행.
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

load_dotenv()

# ─────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────
OUTPUT_DIR   = Path("meta_output")
IG_DATA_FILE = OUTPUT_DIR / "instagram_data.json"
IG_USERNAME  = os.getenv("IG_USERNAME", "")
IG_PASSWORD  = os.getenv("IG_PASSWORD", "")
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            OUTPUT_DIR / f"instagram_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────
# CTA 감지
# ─────────────────────────────────────────────────
_CTA_KEYWORDS = [
    "프로필 링크", "링크는 프로필", "바이오 링크", "링크 클릭",
    "자세한 내용은", "구매는", "구매하기", "지금 구매", "지금 바로",
    "신청하기", "예약하기", "무료 체험", "무료 상담",
    "홈페이지", "웹사이트", "바로가기", "공식 홈", "스토어",
    "클릭하세요", "확인하세요", "쇼핑하기", "장바구니",
]

def detect_cta(caption: str) -> bool:
    if not caption:
        return False
    if re.search(r"https?://", caption):
        return True
    lo = caption.lower()
    return any(kw.lower() in lo for kw in _CTA_KEYWORDS)


# ─────────────────────────────────────────────────
# 바이럴 점수
# ─────────────────────────────────────────────────
def calc_viral_score(views: int, likes: int, comments: int,
                     post_date_str: str) -> float:
    try:
        post_dt = datetime.strptime(post_date_str, "%Y-%m-%d").date()
        days = max((date.today() - post_dt).days, 1)
    except Exception:
        days = 30
    return round((views * 1 + likes * 10 + comments * 50) / days, 2)


# ─────────────────────────────────────────────────
# Meta JSON 로드 + Instagram URL 추출
# ─────────────────────────────────────────────────
def load_latest_meta_json() -> dict:
    """최신 meta_all_categories_*.json 파일 반환"""
    filtered = list(OUTPUT_DIR.glob("meta_all_categories_filtered_*.json"))
    all_files = list(OUTPUT_DIR.glob("meta_all_categories_*.json"))
    files = filtered if filtered else all_files
    if not files:
        raise FileNotFoundError("meta_output/ 에 광고 JSON 파일이 없습니다.")
    latest = max(files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Meta JSON 로드: {latest}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_instagram_urls(meta_data: dict) -> list[dict]:
    """광고 데이터에서 Instagram 관련 정보 추출"""
    items = []
    for cat_name, cat_data in meta_data.get("results", {}).items():
        for q_result in cat_data.get("results_by_query", {}).values():
            for ad in q_result.get("ads", []):
                ad_url = ad.get("ad_library_url", "")
                # Instagram 이 게재 플랫폼에 포함된 광고
                platforms = ad.get("platforms", [])
                if "Instagram" not in platforms:
                    continue
                items.append({
                    "ad_library_url": ad_url,
                    "advertiser":     ad.get("advertiser", ""),
                    "category":       cat_name,
                    # 랜딩페이지 URL 에서 IG 링크 추출 시도
                    "landing_url":    ad.get("landing_page_url", ""),
                })
    logger.info(f"Instagram 플랫폼 광고 {len(items)}개 발견")
    return items


# ─────────────────────────────────────────────────
# Selenium 드라이버
# ─────────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )
    driver.execute_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return driver


def ig_login(driver: webdriver.Chrome) -> bool:
    """Instagram 로그인 (IG_USERNAME / IG_PASSWORD 설정 시)"""
    if not IG_USERNAME or not IG_PASSWORD:
        logger.info("IG 계정 미설정 — 비로그인 모드로 진행")
        return False
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(IG_USERNAME)
        driver.find_element(By.NAME, "password").send_keys(IG_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)
        logger.info("Instagram 로그인 완료")
        return True
    except Exception as e:
        logger.warning(f"Instagram 로그인 실패: {e}")
        return False


# ─────────────────────────────────────────────────
# 단일 Instagram 포스트 스크래핑
# ─────────────────────────────────────────────────
def _parse_metric(text: str) -> int:
    """'1.2만', '3,456', '15K' → int 변환"""
    text = text.replace(",", "").strip()
    if "만" in text:
        return int(float(text.replace("만", "")) * 10000)
    if "천" in text:
        return int(float(text.replace("천", "")) * 1000)
    if "K" in text.upper():
        return int(float(text.upper().replace("K", "")) * 1000)
    if "M" in text.upper():
        return int(float(text.upper().replace("M", "")) * 1_000_000)
    try:
        return int(re.sub(r"[^\d]", "", text))
    except ValueError:
        return 0


def scrape_ig_post(driver: webdriver.Chrome, ig_url: str) -> Optional[dict]:
    """Instagram 포스트 1건 스크래핑 → dict or None"""
    try:
        driver.get(ig_url)
        wait = WebDriverWait(driver, 12)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        time.sleep(random.uniform(2.0, 3.5))

        result = {
            "instagram_url":      ig_url,
            "instagram_views":    0,
            "instagram_likes":    0,
            "instagram_comments": 0,
            "post_date":          "",
            "caption_text":       "",
            "has_cta":            False,
            "viral_score":        0.0,
        }

        # 캡션
        try:
            caption_el = driver.find_element(
                By.CSS_SELECTOR, "article h1, article div[data-testid='post-comment-root'] span"
            )
            result["caption_text"] = caption_el.text.strip()
        except NoSuchElementException:
            pass

        # 좋아요 수 (로그인 필요할 수 있음)
        try:
            like_el = driver.find_element(
                By.CSS_SELECTOR,
                "section span[class*='x193iq5w'], a[href*='liked_by'] span"
            )
            result["instagram_likes"] = _parse_metric(like_el.text)
        except NoSuchElementException:
            pass

        # 조회수 (릴스/비디오)
        try:
            view_el = driver.find_element(
                By.XPATH,
                "//*[contains(@class,'view') or contains(text(),'회 재생') or contains(text(),'views')]"
            )
            result["instagram_views"] = _parse_metric(
                re.sub(r"[^\d만천KkMm,.]", "", view_el.text)
            )
        except NoSuchElementException:
            pass

        # 댓글 수
        try:
            comment_els = driver.find_elements(
                By.CSS_SELECTOR, "ul li[role='menuitem'], div[data-testid='comment']"
            )
            result["instagram_comments"] = len(comment_els)
        except Exception:
            pass

        # 게시일 (<time datetime="...">)
        try:
            time_el = driver.find_element(By.CSS_SELECTOR, "article time[datetime]")
            dt_str  = time_el.get_attribute("datetime")
            result["post_date"] = dt_str[:10]          # YYYY-MM-DD
        except NoSuchElementException:
            pass

        # CTA + 바이럴 점수
        result["has_cta"] = detect_cta(result["caption_text"])
        if result["post_date"]:
            result["viral_score"] = calc_viral_score(
                result["instagram_views"],
                result["instagram_likes"],
                result["instagram_comments"],
                result["post_date"],
            )

        return result

    except TimeoutException:
        logger.warning(f"타임아웃: {ig_url}")
        return None
    except WebDriverException as e:
        logger.warning(f"WebDriver 오류 ({ig_url}): {e}")
        return None


# ─────────────────────────────────────────────────
# 기존 데이터 로드 / 저장
# ─────────────────────────────────────────────────
def load_existing_ig_data() -> dict:
    if IG_DATA_FILE.exists():
        with open(IG_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("data", {})
    return {}


def save_ig_data(data: dict):
    OUTPUT_DIR.mkdir(exist_ok=True)
    payload = {"last_updated": datetime.now().isoformat(), "data": data}
    with open(IG_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(f"저장 완료: {IG_DATA_FILE}  (총 {len(data)}건)")


# ─────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Instagram 데이터 업데이트 시작")
    logger.info("=" * 60)

    # 1) Meta 광고 JSON 로드
    meta_data = load_latest_meta_json()
    ig_items  = extract_instagram_urls(meta_data)

    if not ig_items:
        logger.warning("Instagram 플랫폼 광고가 없습니다. 종료.")
        return

    # 2) 기존 저장 데이터 로드 (증분 업데이트)
    existing = load_existing_ig_data()
    logger.info(f"기존 IG 데이터: {len(existing)}건 / 신규 대상: {len(ig_items)}건")

    # 3) Selenium 드라이버 시작
    driver = build_driver()
    ig_login(driver)

    updated = 0
    skipped = 0

    try:
        for idx, item in enumerate(ig_items, 1):
            ad_url     = item["ad_library_url"]
            ig_url     = item.get("landing_url", "")

            # Instagram URL 패턴 확인
            if not ig_url or "instagram.com" not in ig_url:
                # 랜딩 URL 에서 IG 링크 탐색 실패 → 기존 데이터 재활용
                skipped += 1
                continue

            # 이미 수집된 광고는 7일 주기로만 갱신
            if ad_url in existing:
                prev_date = existing[ad_url].get("collected_at", "")
                if prev_date:
                    try:
                        prev_dt = datetime.fromisoformat(prev_date)
                        if (datetime.now() - prev_dt).days < 7:
                            skipped += 1
                            continue
                    except Exception:
                        pass

            logger.info(f"[{idx}/{len(ig_items)}] 수집 중: {ig_url}")
            result = scrape_ig_post(driver, ig_url)

            if result:
                result["collected_at"] = datetime.now().isoformat()
                result["advertiser"]   = item["advertiser"]
                result["category"]     = item["category"]
                existing[ad_url] = result
                updated += 1
            else:
                skipped += 1

            # 요청 간 랜덤 딜레이 (탐지 회피)
            time.sleep(random.uniform(3.0, 6.0))

            # 100건마다 중간 저장
            if updated % 100 == 0:
                save_ig_data(existing)

    finally:
        driver.quit()

    # 4) 바이럴 점수 전체 재계산 (post_date 기준일 변경 반영)
    logger.info("바이럴 점수 전체 재계산 중...")
    for ad_url, rec in existing.items():
        if rec.get("post_date"):
            rec["viral_score"] = calc_viral_score(
                rec.get("instagram_views",    0),
                rec.get("instagram_likes",    0),
                rec.get("instagram_comments", 0),
                rec["post_date"],
            )

    # 5) 최종 저장
    save_ig_data(existing)

    logger.info(f"완료 — 업데이트: {updated}건 / 스킵: {skipped}건")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
