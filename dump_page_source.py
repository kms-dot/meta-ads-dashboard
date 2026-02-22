"""
전체 페이지 소스 덤프 및 분석
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    return driver

def main():
    driver = None
    try:
        driver = setup_driver()

        # Meta 광고 라이브러리 접속
        url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&q=메디큐브&search_type=keyword_unordered"

        print(f"URL 접속: {url}")
        driver.get(url)

        print("페이지 로딩 대기...")
        time.sleep(10)  # 충분히 대기

        # 스크롤
        print("스크롤 1회...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # 페이지 소스 가져오기
        print("페이지 소스 가져오기...")
        page_source = driver.page_source

        # 저장
        output_dir = 'meta_output'
        os.makedirs(output_dir, exist_ok=True)

        filename = f'{output_dir}/full_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)

        print(f"\n페이지 소스 저장: {filename}")
        print(f"크기: {len(page_source)} bytes")

        # 간단한 분석
        print("\n간단한 분석:")
        print(f"  '/ads/library/?id=' 포함 횟수: {page_source.count('/ads/library/?id=')}")
        print(f"  'scontent' (이미지) 포함 횟수: {page_source.count('scontent')}")
        print(f"  '게재 시작' 포함 횟수: {page_source.count('게재 시작')}")
        print(f"  'Started running' 포함 횟수: {page_source.count('Started running')}")
        print(f"  'facebook.com/' 링크 포함 횟수: {page_source.count('facebook.com/')}")

    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\n브라우저 종료...")
            driver.quit()

if __name__ == "__main__":
    main()
