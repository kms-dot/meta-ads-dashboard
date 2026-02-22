"""
Meta 광고 라이브러리 HTML 구조 진단 스크립트

실제 광고 카드의 HTML을 덤프하고 분석합니다.
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

def find_ad_containers(driver):
    """광고 컨테이너 찾기 (다양한 방법 시도)"""

    strategies = [
        {
            'name': '방법1: href 기반 (광고 라이브러리 링크)',
            'selector': '//a[contains(@href, "/ads/library/?id=")]/ancestor::div[3]',
            'by': By.XPATH
        },
        {
            'name': '방법2: 구조 기반 (광고 카드 구조)',
            'selector': '//div[@role="article"]',
            'by': By.XPATH
        },
        {
            'name': '방법3: 광고주 링크 기반',
            'selector': '//a[contains(@href, "facebook.com/")]/../..',
            'by': By.XPATH
        },
        {
            'name': '방법4: 이미지/비디오 포함 카드',
            'selector': '//img[@alt]/ancestor::div[contains(@class, "x1n2onr6")]',
            'by': By.XPATH
        },
        {
            'name': '방법5: CSS 클래스 기반 (기존)',
            'selector': 'div[class*="x1n2onr6"]',
            'by': By.CSS_SELECTOR
        }
    ]

    results = {}

    for strategy in strategies:
        try:
            print(f"\n{strategy['name']}")
            elements = driver.find_elements(strategy['by'], strategy['selector'])
            count = len(elements)
            results[strategy['name']] = {
                'count': count,
                'selector': strategy['selector'],
                'by': strategy['by']
            }
            print(f"  발견된 요소: {count}개")

            if count > 0 and count < 2000:  # 너무 많지 않으면 좋은 후보
                return elements[:5]  # 처음 5개만 반환

        except Exception as e:
            print(f"  오류: {e}")
            results[strategy['name']] = {'error': str(e)}

    print("\n결과 요약:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    return []

def dump_ad_card_html(element, index):
    """광고 카드 HTML 덤프"""
    try:
        html = element.get_attribute('outerHTML')

        # 파일 저장
        output_dir = 'meta_output/html_dumps'
        os.makedirs(output_dir, exist_ok=True)

        filename = f'{output_dir}/ad_card_{index}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  카드 #{index} HTML 저장: {filename}")

        return html
    except Exception as e:
        print(f"  카드 #{index} HTML 덤프 실패: {e}")
        return None

def analyze_ad_card(driver, element, index):
    """광고 카드 구조 분석"""

    print(f"\n{'='*60}")
    print(f"광고 카드 #{index} 분석")
    print('='*60)

    # HTML 덤프
    html = dump_ad_card_html(element, index)

    if not html:
        return None

    analysis = {
        'index': index,
        'html_length': len(html),
        'elements': {}
    }

    # 다양한 요소 찾기 시도
    searches = {
        '광고주명 (링크 텍스트)': [
            './/a[contains(@href, "facebook.com/")]',
            './/a[@role="link"]',
            './/span[contains(@class, "x1lliihq")]'
        ],
        '광고 라이브러리 URL': [
            './/a[contains(@href, "/ads/library/?id=")]',
            './/a[contains(text(), "광고 세부정보")]'
        ],
        '게재 시작일': [
            './/span[contains(text(), "게재 시작")]',
            './/span[contains(text(), "Started running on")]',
            './/div[contains(text(), "20")]'  # 날짜 패턴
        ],
        '썸네일 이미지': [
            './/img[@alt]',
            './/img[contains(@src, "scontent")]'
        ],
        '비디오': [
            './/video',
            './/div[contains(@aria-label, "video")]'
        ],
        '광고 텍스트': [
            './/div[@dir="auto"]',
            './/span[contains(@class, "x193iq5w")]'
        ],
        '플랫폼 정보': [
            './/span[contains(text(), "Facebook")]',
            './/span[contains(text(), "Instagram")]'
        ],
        '노출수 정보': [
            './/span[contains(text(), "노출수")]',
            './/span[contains(text(), "Impressions")]',
            './/span[contains(text(), "적음")]'
        ]
    }

    for element_name, xpaths in searches.items():
        print(f"\n{element_name}:")
        found = False

        for xpath in xpaths:
            try:
                results = element.find_elements(By.XPATH, xpath)

                if results:
                    found = True
                    print(f"  [OK] 발견 (XPath: {xpath})")
                    print(f"    개수: {len(results)}")

                    # 처음 3개 요소의 텍스트/속성 출력
                    for i, result in enumerate(results[:3]):
                        try:
                            text = result.text.strip()[:100]  # 처음 100자
                            href = result.get_attribute('href')
                            src = result.get_attribute('src')

                            if text:
                                print(f"    [{i+1}] 텍스트: {text}")
                            if href:
                                print(f"    [{i+1}] href: {href[:100]}")
                            if src:
                                print(f"    [{i+1}] src: {src[:100]}")
                        except:
                            pass

                    # 분석 결과에 저장
                    analysis['elements'][element_name] = {
                        'xpath': xpath,
                        'count': len(results),
                        'found': True
                    }

                    break  # 첫 번째 성공한 XPath 사용

            except Exception as e:
                pass

        if not found:
            print(f"  [X] 발견 안됨")
            analysis['elements'][element_name] = {'found': False}

    return analysis

def generate_selector_config(analyses):
    """분석 결과 기반으로 새로운 셀렉터 설정 생성"""

    print(f"\n{'='*60}")
    print("새로운 셀렉터 설정 생성")
    print('='*60)

    # 가장 많이 발견된 XPath 추출
    selector_stats = {}

    for analysis in analyses:
        for element_name, data in analysis['elements'].items():
            if data.get('found'):
                xpath = data.get('xpath')
                if xpath:
                    if element_name not in selector_stats:
                        selector_stats[element_name] = {}

                    if xpath not in selector_stats[element_name]:
                        selector_stats[element_name][xpath] = 0

                    selector_stats[element_name][xpath] += 1

    # 새로운 설정 파일 생성
    new_config = {
        'selectors': {},
        'notes': '진단 스크립트로 생성된 설정 (구조 기반 XPath 우선)'
    }

    print("\n추천 셀렉터:")

    for element_name, xpaths in selector_stats.items():
        # 가장 많이 발견된 XPath 정렬
        sorted_xpaths = sorted(xpaths.items(), key=lambda x: x[1], reverse=True)

        if sorted_xpaths:
            best_xpath = sorted_xpaths[0][0]
            count = sorted_xpaths[0][1]

            print(f"\n{element_name}:")
            print(f"  XPath: {best_xpath}")
            print(f"  성공률: {count}/{len(analyses)}")

            # 키 이름 매핑
            key_mapping = {
                '광고주명 (링크 텍스트)': 'advertiser',
                '광고 라이브러리 URL': 'ad_link',
                '게재 시작일': 'start_date',
                '썸네일 이미지': 'thumbnail',
                '비디오': 'video',
                '광고 텍스트': 'ad_text',
                '플랫폼 정보': 'platforms',
                '노출수 정보': 'impression'
            }

            key = key_mapping.get(element_name)
            if key:
                # XPath 리스트로 저장 (Fallback 전략)
                new_config['selectors'][key] = [best_xpath]

                # 2등, 3등도 추가
                for xpath, cnt in sorted_xpaths[1:3]:
                    new_config['selectors'][key].append(xpath)

    # 광고 카드 컨테이너 셀렉터 추가
    new_config['selectors']['ad_card'] = [
        '//a[contains(@href, "/ads/library/?id=")]/ancestor::div[3]',
        '//div[@role="article"]'
    ]

    # 설정 파일 저장
    output_file = 'config/meta_selectors_new.json'
    os.makedirs('config', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)

    print(f"\n새로운 설정 저장: {output_file}")

    return new_config

def main():
    """메인 실행"""

    print("="*60)
    print("Meta 광고 라이브러리 HTML 구조 진단 시작")
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

        # 광고 컨테이너 찾기
        print("\n광고 컨테이너 탐색 중...")
        ad_containers = find_ad_containers(driver)

        if not ad_containers:
            print("\n[ERROR] 광고 컨테이너를 찾을 수 없습니다.")

            # 전체 페이지 HTML 덤프
            print("\n전체 페이지 HTML 저장 중...")
            page_html = driver.page_source

            output_dir = 'meta_output/html_dumps'
            os.makedirs(output_dir, exist_ok=True)

            filename = f'{output_dir}/full_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_html)

            print(f"전체 페이지 HTML 저장: {filename}")
            print("HTML 파일을 직접 확인하여 구조를 분석하세요.")

            return

        print(f"\n[OK] {len(ad_containers)}개의 광고 카드 발견")

        # 각 광고 카드 분석
        analyses = []

        for i, container in enumerate(ad_containers, 1):
            analysis = analyze_ad_card(driver, container, i)
            if analysis:
                analyses.append(analysis)

            # 3개만 분석
            if i >= 3:
                break

        # 새로운 셀렉터 설정 생성
        if analyses:
            new_config = generate_selector_config(analyses)

            print("\n" + "="*60)
            print("[OK] 진단 완료!")
            print("="*60)
            print("\n다음 파일들을 확인하세요:")
            print("1. meta_output/html_dumps/*.html - 광고 카드 HTML")
            print("2. config/meta_selectors_new.json - 새로운 셀렉터 설정")
            print("\n새로운 설정을 테스트하려면:")
            print("  python test_new_selectors.py")

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
