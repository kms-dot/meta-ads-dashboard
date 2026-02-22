"""
페이지 구조 분석 - BeautifulSoup 사용
"""

from bs4 import BeautifulSoup
import os

def main():
    # HTML 파일 읽기
    html_file = 'meta_output/full_page_20260211_120851.html'

    if not os.path.exists(html_file):
        print(f"파일을 찾을 수 없습니다: {html_file}")
        return

    print(f"파일 분석 중: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print(f"파일 크기: {len(html_content)} bytes")

    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    print("\n=== 광고 관련 요소 찾기 ===\n")

    # 1. "게재 시작" 텍스트 포함 요소
    print("1. '게재 시작' 텍스트 포함 요소:")
    date_elements = soup.find_all(text=lambda t: t and '게재 시작' in str(t))
    print(f"   발견: {len(date_elements)}개")

    for i, elem in enumerate(date_elements[:3], 1):
        parent = elem.parent
        print(f"\n   [{i}] 텍스트: {str(elem).strip()[:100]}")
        print(f"       부모 태그: {parent.name if parent else 'None'}")
        if parent and parent.has_attr('class'):
            print(f"       부모 클래스: {parent.get('class')}")

        # 조상 찾기
        ancestors = list(parent.parents)[:5] if parent else []
        print(f"       조상 경로: {' > '.join([a.name for a in reversed(ancestors)])}")

    # 2. 이미지 요소 (scontent)
    print("\n2. 이미지 요소 (scontent):")
    images = soup.find_all('img', src=lambda x: x and 'scontent' in x)
    print(f"   발견: {len(images)}개")

    for i, img in enumerate(images[:3], 1):
        print(f"\n   [{i}] src: {img.get('src')[:80]}")
        print(f"       alt: {img.get('alt', 'None')}")
        if img.has_attr('class'):
            print(f"       class: {img.get('class')}")

        # 부모 찾기
        parent = img.parent
        if parent:
            print(f"       부모 태그: {parent.name}")
            if parent.has_attr('class'):
                print(f"       부모 클래스: {parent.get('class')}")

    # 3. facebook.com/ 링크 (광고주)
    print("\n3. facebook.com/ 링크:")
    advertiser_links = soup.find_all('a', href=lambda x: x and 'facebook.com/' in x and '/ads/library' not in x)
    print(f"   발견: {len(advertiser_links)}개")

    for i, link in enumerate(advertiser_links[:5], 1):
        text = link.get_text(strip=True)
        if text and len(text) > 3 and len(text) < 100:
            print(f"\n   [{i}] 텍스트: {text[:50]}")
            print(f"       href: {link.get('href')[:80]}")
            if link.has_attr('class'):
                print(f"       class: {link.get('class')}")

    # 4. 광고 구조 찾기 - 큰 div 블록
    print("\n4. 광고 카드로 보이는 구조 분석:")

    # "게재 시작"과 이미지를 모두 포함하는 div 찾기
    ad_containers = []

    for date_elem in date_elements[:10]:
        # 조상 중에서 충분히 큰 div 찾기
        current = date_elem.parent

        while current:
            if current.name == 'div':
                html_str = str(current)

                # 광고 카드 조건: 이미지 + 날짜 + 링크
                has_image = 'scontent' in html_str or '<img' in html_str
                has_date = '게재 시작' in html_str
                has_link = 'facebook.com/' in html_str

                if has_image and has_date and has_link and len(html_str) > 2000:
                    # 중복 체크
                    if current not in ad_containers:
                        ad_containers.append(current)
                        break

            current = current.parent

    print(f"   발견: {len(ad_containers)}개")

    # 광고 카드 저장
    output_dir = 'meta_output/analyzed_cards'
    os.makedirs(output_dir, exist_ok=True)

    for i, container in enumerate(ad_containers[:3], 1):
        filename = f'{output_dir}/ad_card_analyzed_{i}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(container.prettify()))
        print(f"   [{i}] 저장: {filename} (크기: {len(str(container))} bytes)")

        # 간단한 분석
        container_soup = BeautifulSoup(str(container), 'html.parser')

        # 링크 분석
        links = container_soup.find_all('a', href=True)
        print(f"       - 링크 개수: {len(links)}")

        # 광고주 링크 찾기
        adv_links = [l for l in links if 'facebook.com/' in l.get('href') and '/ads/library' not in l.get('href')]
        if adv_links:
            print(f"       - 광고주 링크: {adv_links[0].get_text(strip=True)[:30]}")

        # 이미지
        imgs = container_soup.find_all('img', src=lambda x: x and 'scontent' in x)
        print(f"       - 이미지 개수: {len(imgs)}")

    print("\n=== 분석 완료 ===")
    print(f"광고 카드 HTML 저장: {output_dir}/")

if __name__ == "__main__":
    main()
