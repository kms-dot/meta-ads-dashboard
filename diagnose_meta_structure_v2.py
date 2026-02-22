"""
Meta 광고 라이브러리 HTML 구조 진단 스크립트 V2

실제 광고 카드의 HTML을 더 정확하게 덤프하고 분석합니다.
광고 라이브러리 링크를 포함한 전체 광고 카드를 찾습니다.
"""

import os
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from bs4 import BeautifulSoup

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    # 헤드리스 모드 비활성화 (디버깅용)
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    return driver

def wait_for_page_load(driver, timeout=15):
    """페이지 로딩 대기"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(3)  # 추가 대기
        return True
    except Exception as e:
        print(f"페이지 로딩 대기 중 오류: {e}")
        return False

def scroll_to_load_ads(driver, max_scrolls=3):
    """스크롤하여 광고 로드"""
    print(f"스크롤 시작 (최대 {max_scrolls}회)...")

    for i in range(max_scrolls):
        # 현재 높이
        current_height = driver.execute_script("return document.body.scrollHeight")

        # 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"  스크롤 {i+1}/{max_scrolls}")

        # 대기
        time.sleep(3)

        # 새 높이
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == current_height:
            print("  더 이상 로드할 콘텐츠 없음")
            break

def find_ad_library_links(driver):
    """광고 라이브러리 링크를 먼저 찾기"""

    print("\n광고 라이브러리 링크 탐색 중...")

    strategies = [
        {
            'name': '방법1: /ads/library/?id= 패턴',
            'xpath': '//a[contains(@href, "/ads/library/?id=")]',
        },
        {
            'name': '방법2: 광고 세부정보 텍스트',
            'xpath': '//a[contains(text(), "광고 세부정보")]',
        },
        {
            'name': '방법3: See ad details 텍스트',
            'xpath': '//a[contains(text(), "See ad details")]',
        },
        {
            'name': '방법4: aria-label 속성',
            'xpath': '//a[contains(@aria-label, "광고") or contains(@aria-label, "ad")]',
        }
    ]

    all_links = []

    for strategy in strategies:
        try:
            print(f"\n{strategy['name']}")
            elements = driver.find_elements(By.XPATH, strategy['xpath'])
            print(f"  발견된 링크: {len(elements)}개")

            if elements:
                for elem in elements[:3]:  # 처음 3개만 확인
                    href = elem.get_attribute('href')
                    text = elem.text.strip()
                    print(f"    - href: {href[:80] if href else 'None'}")
                    print(f"      text: {text[:50] if text else 'None'}")

                all_links.extend(elements)

        except Exception as e:
            print(f"  오류: {e}")

    return all_links

def find_ad_cards_from_links(driver, ad_links):
    """광고 라이브러리 링크로부터 광고 카드 찾기"""

    print(f"\n광고 라이브러리 링크 {len(ad_links)}개로부터 광고 카드 찾기...")

    ad_cards = []

    for i, link in enumerate(ad_links[:5]):  # 처음 5개만
        try:
            # 다양한 ancestor 레벨 시도
            for level in range(3, 10):
                try:
                    xpath = f'//a[@href="{link.get_attribute("href")}"]/ancestor::*[{level}]'
                    containers = driver.find_elements(By.XPATH, xpath)

                    if containers:
                        container = containers[0]
                        html = container.get_attribute('outerHTML')

                        # 광고 카드로 적합한지 검사 (충분한 콘텐츠 포함)
                        if len(html) > 1000:  # 최소 크기
                            # BeautifulSoup으로 파싱
                            soup = BeautifulSoup(html, 'html.parser')

                            # 필수 요소 체크
                            has_link = soup.find('a', href=lambda x: x and '/ads/library/?id=' in x)
                            has_img_or_video = soup.find('img') or soup.find('video')

                            if has_link:
                                print(f"  링크 #{i+1}: ancestor 레벨 {level}에서 발견 (크기: {len(html)} bytes)")
                                ad_cards.append(container)
                                break

                except:
                    continue

        except Exception as e:
            print(f"  링크 #{i+1} 처리 중 오류: {e}")

    return ad_cards

def analyze_ad_card_detailed(driver, element, index):
    """광고 카드 상세 분석"""

    print(f"\n{'='*60}")
    print(f"광고 카드 #{index} 상세 분석")
    print('='*60)

    # HTML 덤프
    html = element.get_attribute('outerHTML')

    # 파일 저장
    output_dir = 'meta_output/html_dumps_v2'
    os.makedirs(output_dir, exist_ok=True)

    filename = f'{output_dir}/ad_card_{index}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  HTML 저장: {filename}")
    print(f"  HTML 크기: {len(html)} bytes")

    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(html, 'html.parser')

    analysis = {
        'index': index,
        'html_length': len(html),
        'elements': {}
    }

    # 광고 라이브러리 링크
    print("\n1. 광고 라이브러리 링크:")
    ad_links = soup.find_all('a', href=lambda x: x and '/ads/library/?id=' in x)
    if ad_links:
        for link in ad_links[:2]:
            print(f"  [OK] {link.get('href')[:100]}")
            print(f"       텍스트: {link.get_text(strip=True)[:50]}")
        analysis['elements']['ad_library_link'] = {
            'found': True,
            'count': len(ad_links),
            'sample_href': ad_links[0].get('href')
        }
    else:
        print("  [X] 발견 안됨")
        analysis['elements']['ad_library_link'] = {'found': False}

    # 광고주명
    print("\n2. 광고주명:")
    # facebook.com/ 링크 찾기
    advertiser_links = soup.find_all('a', href=lambda x: x and 'facebook.com/' in x and '/ads/library/' not in x)
    if advertiser_links:
        for link in advertiser_links[:2]:
            text = link.get_text(strip=True)
            if text and len(text) > 0:
                print(f"  [OK] {text}")
                print(f"       href: {link.get('href')[:80]}")
        analysis['elements']['advertiser'] = {
            'found': True,
            'count': len(advertiser_links)
        }
    else:
        print("  [X] 발견 안됨")
        analysis['elements']['advertiser'] = {'found': False}

    # 날짜 정보
    print("\n3. 날짜 정보:")
    # "게재 시작", "Started running on" 등의 텍스트 찾기
    date_patterns = ['게재 시작', 'Started running on', '20', '년', '월', '일']
    date_texts = []

    for text_elem in soup.find_all(text=True):
        text = str(text_elem).strip()
        if any(pattern in text for pattern in date_patterns):
            if len(text) > 5 and len(text) < 100:
                date_texts.append(text)

    if date_texts:
        for dt in date_texts[:3]:
            print(f"  [OK] {dt}")
        analysis['elements']['date'] = {
            'found': True,
            'count': len(date_texts)
        }
    else:
        print("  [X] 발견 안됨")
        analysis['elements']['date'] = {'found': False}

    # 이미지/비디오
    print("\n4. 미디어:")
    images = soup.find_all('img', src=True)
    videos = soup.find_all('video', src=True)

    print(f"  이미지: {len(images)}개")
    for img in images[:2]:
        src = img.get('src', '')
        if 'scontent' in src or 'fbcdn' in src:
            print(f"    - {src[:80]}")

    print(f"  비디오: {len(videos)}개")
    for vid in videos[:2]:
        print(f"    - {vid.get('src', '')[:80]}")

    analysis['elements']['media'] = {
        'images': len(images),
        'videos': len(videos)
    }

    # 플랫폼 정보
    print("\n5. 플랫폼 정보:")
    platform_keywords = ['Facebook', 'Instagram', 'Messenger', '페이스북', '인스타그램']
    platform_texts = []

    for text_elem in soup.find_all(text=True):
        text = str(text_elem).strip()
        if any(keyword in text for keyword in platform_keywords):
            if len(text) < 100:
                platform_texts.append(text)

    if platform_texts:
        for pt in platform_texts[:3]:
            print(f"  [OK] {pt}")
        analysis['elements']['platform'] = {
            'found': True,
            'count': len(platform_texts)
        }
    else:
        print("  [X] 발견 안됨")
        analysis['elements']['platform'] = {'found': False}

    # 노출수 정보
    print("\n6. 노출수 정보:")
    impression_keywords = ['노출수', 'Impressions', '적음', 'Low', 'Fewer']
    impression_texts = []

    for text_elem in soup.find_all(text=True):
        text = str(text_elem).strip()
        if any(keyword.lower() in text.lower() for keyword in impression_keywords):
            if len(text) < 100:
                impression_texts.append(text)

    if impression_texts:
        for it in impression_texts[:3]:
            print(f"  [OK] {it}")
        analysis['elements']['impression'] = {
            'found': True,
            'count': len(impression_texts)
        }
    else:
        print("  [X] 발견 안됨")
        analysis['elements']['impression'] = {'found': False}

    return analysis

def generate_xpath_selectors(analyses):
    """분석 결과 기반 XPath 셀렉터 생성"""

    print(f"\n{'='*60}")
    print("새로운 XPath 셀렉터 생성")
    print('='*60)

    new_config = {
        'selectors': {},
        'notes': '진단 스크립트 V2로 생성 - 실제 HTML 구조 기반'
    }

    # 광고 카드 컨테이너
    new_config['selectors']['ad_card'] = [
        '//a[contains(@href, "/ads/library/?id=")]/ancestor::*[6]',
        '//a[contains(@href, "/ads/library/?id=")]/ancestor::*[7]',
        '//a[contains(@href, "/ads/library/?id=")]/ancestor::*[5]',
    ]

    # 광고 라이브러리 링크
    new_config['selectors']['ad_link'] = [
        './/a[contains(@href, "/ads/library/?id=")]',
        './/a[contains(text(), "광고 세부정보")]',
        './/a[contains(text(), "See ad details")]',
    ]

    # 광고주명
    new_config['selectors']['advertiser'] = [
        './/a[contains(@href, "facebook.com/") and not(contains(@href, "/ads/library/"))]',
        './/span[contains(@class, "x8t9es0")]//following-sibling::span',
    ]

    # 날짜
    new_config['selectors']['start_date'] = [
        './/span[contains(text(), "게재 시작")]',
        './/span[contains(text(), "Started running on")]',
        './/*[contains(text(), "년") and contains(text(), "월")]',
    ]

    # 썸네일
    new_config['selectors']['thumbnail'] = [
        './/img[contains(@src, "scontent")]',
        './/img[contains(@src, "fbcdn")]',
        './/img[@alt]',
    ]

    # 비디오
    new_config['selectors']['video'] = [
        './/video[@src]',
        './/video',
    ]

    # 광고 텍스트
    new_config['selectors']['ad_text'] = [
        './/div[@style and contains(@style, "white-space")]',
        './/span[contains(@class, "x8t9es0")]',
    ]

    # 플랫폼
    new_config['selectors']['platforms'] = [
        './/*[contains(text(), "Facebook") or contains(text(), "Instagram")]',
        './/*[contains(text(), "페이스북") or contains(text(), "인스타그램")]',
    ]

    # 노출수
    new_config['selectors']['impression'] = [
        './/*[contains(text(), "노출수")]',
        './/*[contains(text(), "Impressions")]',
    ]

    # 설정 파일 저장
    output_file = 'config/meta_selectors_v2.json'
    os.makedirs('config', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)

    print(f"\n새로운 설정 저장: {output_file}")

    return new_config

def main():
    """메인 실행"""

    print("="*60)
    print("Meta 광고 라이브러리 HTML 구조 진단 V2")
    print("="*60)

    driver = None

    try:
        # 드라이버 설정
        driver = setup_driver()

        # Meta 광고 라이브러리 접속
        search_query = "메디큐브"
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&q={search_query}&search_type=keyword_unordered"

        print(f"\nURL 접속: {url}")
        driver.get(url)

        # 페이지 로딩 대기
        if not wait_for_page_load(driver):
            print("페이지 로딩 실패")
            return

        print("페이지 로딩 완료")

        # 스크롤하여 광고 로드
        scroll_to_load_ads(driver, max_scrolls=3)

        # 1단계: 광고 라이브러리 링크 찾기
        ad_links = find_ad_library_links(driver)

        if not ad_links:
            print("\n[ERROR] 광고 라이브러리 링크를 찾을 수 없습니다.")

            # 전체 페이지 HTML 덤프
            print("\n전체 페이지 HTML 저장 중...")
            page_html = driver.page_source

            output_dir = 'meta_output/html_dumps_v2'
            os.makedirs(output_dir, exist_ok=True)

            filename = f'{output_dir}/full_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_html)

            print(f"전체 페이지 HTML 저장: {filename}")
            return

        print(f"\n[OK] {len(ad_links)}개의 광고 라이브러리 링크 발견")

        # 2단계: 링크로부터 광고 카드 찾기
        ad_cards = find_ad_cards_from_links(driver, ad_links)

        if not ad_cards:
            print("\n[ERROR] 광고 카드를 찾을 수 없습니다.")
            return

        print(f"\n[OK] {len(ad_cards)}개의 광고 카드 발견")

        # 3단계: 각 광고 카드 분석
        analyses = []

        for i, container in enumerate(ad_cards[:3], 1):  # 처음 3개만
            analysis = analyze_ad_card_detailed(driver, container, i)
            if analysis:
                analyses.append(analysis)

        # 4단계: 새로운 셀렉터 설정 생성
        if analyses:
            new_config = generate_xpath_selectors(analyses)

            print("\n" + "="*60)
            print("[OK] 진단 완료!")
            print("="*60)
            print("\n다음 파일들을 확인하세요:")
            print("1. meta_output/html_dumps_v2/*.html - 광고 카드 HTML")
            print("2. config/meta_selectors_v2.json - 새로운 셀렉터 설정")

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\n브라우저 종료...")
            driver.quit()

if __name__ == "__main__":
    main()
