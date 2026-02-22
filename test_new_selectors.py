"""
새로운 셀렉터 테스트 스크립트

실제 Meta 광고 라이브러리에서 새로운 셀렉터의 파싱 성공률을 테스트합니다.
"""

import os
import sys
import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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

def load_selectors():
    """새로운 셀렉터 설정 로드"""
    with open('config/meta_selectors_final.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['selectors']

def find_with_fallback(element, selectors, by=By.XPATH):
    """여러 셀렉터를 시도하며 요소 찾기 (폴백 전략)"""
    for selector in selectors:
        try:
            result = element.find_element(by, selector)
            if result:
                return result
        except:
            continue
    return None

def find_all_with_fallback(element, selectors, by=By.XPATH):
    """여러 셀렉터를 시도하며 요소들 찾기 (폴백 전략)"""
    for selector in selectors:
        try:
            results = element.find_elements(by, selector)
            if results:
                return results
        except:
            continue
    return []

def get_text_safe(element, selectors):
    """텍스트 안전하게 추출"""
    found = find_with_fallback(element, selectors)
    if found:
        return found.text.strip()
    return ""

def get_attribute_safe(element, selectors, attribute):
    """속성 안전하게 추출"""
    found = find_with_fallback(element, selectors)
    if found:
        return found.get_attribute(attribute)
    return ""

def extract_ad_library_id(text):
    """라이브러리 ID 추출"""
    if not text:
        return ""

    # 패턴: "라이브러리 ID: 123456789"
    match = re.search(r'ID[:\s]*(\d+)', text)
    if match:
        return match.group(1)

    return ""

def extract_date(text):
    """날짜 추출 및 파싱"""
    if not text:
        return None

    # 한국어 패턴: 2025. 8. 29.
    pattern = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.'
    match = re.search(pattern, text)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return f"{year}-{month:02d}-{day:02d}"

    return text

def parse_ad_card(driver, card, index, selectors):
    """광고 카드 파싱"""

    result = {
        'index': index,
        'success': {},
        'data': {}
    }

    # 1. 광고주명
    try:
        advertiser_elem = find_with_fallback(card, selectors['advertiser'])
        if advertiser_elem:
            advertiser = advertiser_elem.text.strip() if advertiser_elem.text else advertiser_elem.get_attribute('textContent').strip()
            result['data']['advertiser'] = advertiser
            result['success']['advertiser'] = True
        else:
            result['success']['advertiser'] = False
    except Exception as e:
        result['success']['advertiser'] = False

    # 2. 라이브러리 ID
    try:
        id_text = get_text_safe(card, selectors['ad_library_id'])
        if id_text:
            ad_id = extract_ad_library_id(id_text)
            result['data']['ad_library_id'] = ad_id
            result['success']['ad_library_id'] = True
        else:
            result['success']['ad_library_id'] = False
    except Exception as e:
        result['success']['ad_library_id'] = False

    # 3. 게재 시작일
    try:
        date_text = get_text_safe(card, selectors['start_date'])
        if date_text:
            parsed_date = extract_date(date_text)
            result['data']['start_date'] = parsed_date
            result['success']['start_date'] = True
        else:
            result['success']['start_date'] = False
    except Exception as e:
        result['success']['start_date'] = False

    # 4. 썸네일 이미지
    try:
        thumbnail_elem = find_with_fallback(card, selectors['thumbnail'])
        if thumbnail_elem:
            thumbnail_url = thumbnail_elem.get_attribute('src')
            result['data']['thumbnail_url'] = thumbnail_url
            result['success']['thumbnail'] = True
        else:
            result['success']['thumbnail'] = False
    except Exception as e:
        result['success']['thumbnail'] = False

    # 5. 광고 크리에이티브 이미지
    try:
        creative_elem = find_with_fallback(card, selectors['ad_creative_image'])
        if creative_elem:
            creative_url = creative_elem.get_attribute('src')
            result['data']['ad_creative_image_url'] = creative_url
            result['success']['ad_creative_image'] = True
        else:
            result['success']['ad_creative_image'] = False
    except Exception as e:
        result['success']['ad_creative_image'] = False

    # 6. 광고 텍스트
    try:
        ad_text = get_text_safe(card, selectors['ad_text'])
        if ad_text:
            result['data']['ad_text'] = ad_text[:100]  # 처음 100자만
            result['success']['ad_text'] = True
        else:
            result['success']['ad_text'] = False
    except Exception as e:
        result['success']['ad_text'] = False

    # 7. 광고 링크
    try:
        ad_link_elem = find_with_fallback(card, selectors['ad_link'])
        if ad_link_elem:
            ad_link = ad_link_elem.get_attribute('href')
            result['data']['ad_link'] = ad_link[:100] if ad_link else ""
            result['success']['ad_link'] = True
        else:
            result['success']['ad_link'] = False
    except Exception as e:
        result['success']['ad_link'] = False

    # 8. 상태
    try:
        status_text = get_text_safe(card, selectors['status'])
        if status_text:
            result['data']['status'] = status_text
            result['success']['status'] = True
        else:
            result['success']['status'] = False
    except Exception as e:
        result['success']['status'] = False

    return result

def main():
    """메인 테스트"""

    print("="*60)
    print("새로운 셀렉터 테스트")
    print("="*60)

    driver = None

    try:
        # 드라이버 설정
        driver = setup_driver()

        # 셀렉터 로드
        selectors = load_selectors()
        print(f"\n셀렉터 로드 완료")

        # Meta 광고 라이브러리 접속
        url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&q=메디큐브&search_type=keyword_unordered"

        print(f"\nURL 접속: {url}")
        driver.get(url)

        print("페이지 로딩 대기...")
        time.sleep(10)

        # 스크롤
        print("스크롤 1회...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # 광고 카드 찾기
        print("\n광고 카드 탐색 중...")

        ad_cards = []
        for selector in selectors['ad_card']:
            try:
                cards = driver.find_elements(By.XPATH, selector)
                if cards:
                    print(f"  셀렉터 성공: {selector[:50]}... -> {len(cards)}개 발견")
                    ad_cards = cards
                    break
            except:
                continue

        if not ad_cards:
            print("\n[ERROR] 광고 카드를 찾을 수 없습니다.")
            return

        print(f"\n[OK] {len(ad_cards)}개의 광고 카드 발견")

        # 처음 10개 테스트
        test_count = min(10, len(ad_cards))
        print(f"\n처음 {test_count}개 광고 카드 파싱 테스트...\n")

        results = []
        success_counts = {
            'advertiser': 0,
            'ad_library_id': 0,
            'start_date': 0,
            'thumbnail': 0,
            'ad_creative_image': 0,
            'ad_text': 0,
            'ad_link': 0,
            'status': 0
        }

        for i, card in enumerate(ad_cards[:test_count], 1):
            print(f"{'='*60}")
            print(f"광고 카드 #{i}")
            print(f"{'='*60}")

            result = parse_ad_card(driver, card, i, selectors)
            results.append(result)

            # 성공 여부 출력
            for field, success in result['success'].items():
                if success:
                    success_counts[field] += 1
                    status = "[OK]"
                    value = result['data'].get(field, '')
                    if isinstance(value, str) and len(value) > 80:
                        value = value[:80] + "..."
                    # 인코딩 안전 처리 - ASCII로 변환
                    try:
                        safe_value = str(value).encode('ascii', errors='replace').decode('ascii')
                        print(f"  {status} {field}: {safe_value[:100]}")
                    except:
                        print(f"  {status} {field}: [encoding error]")
                else:
                    print(f"  [X] {field}: failed")

            print()

        # 통계 출력
        print("\n" + "="*60)
        print("파싱 성공률 통계")
        print("="*60)

        for field, count in success_counts.items():
            rate = (count / test_count) * 100
            print(f"  {field}: {count}/{test_count} ({rate:.1f}%)")

        # 결과 저장
        output_dir = 'meta_output/test_results'
        os.makedirs(output_dir, exist_ok=True)

        output_file = f'{output_dir}/test_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_count': test_count,
                'results': results,
                'success_counts': success_counts,
                'success_rates': {k: f"{(v/test_count)*100:.1f}%" for k, v in success_counts.items()}
            }, f, indent=2, ensure_ascii=False)

        print(f"\n결과 저장: {output_file}")

        print("\n" + "="*60)
        print("[OK] 테스트 완료!")
        print("="*60)

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
