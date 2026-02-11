"""
카테고리별로 부적합한 광고를 필터링하는 스크립트
"""
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# 카테고리별 제외 키워드 (광고주명 또는 광고 텍스트에 포함시 제외)
EXCLUDE_KEYWORDS = {
    '스킨케어': [
        '영어', '일본어', '중국어', '학원', '교육', '과외', '강의', 'english', 'TOEIC', 'TOEFL',
        '고양이', '강아지', '펫', '반려동물', '사료', '모래',
        '게임', '앱', '어플', '플레이',
        '부동산', '아파트', '오피스텔', '재테크', '투자',
        '식품', '음식', '먹거리', '쿠폰', '배달',
        '가구', '침대', '소파', '책상', '의자',
        '여행', '항공', '호텔', '숙소'
    ],
    '헤어케어': [
        '피부', '얼굴', '스킨', '로션', '크림', '앰플', '세럼',
        '영어', '일본어', '중국어', '학원', '교육', '과외', '강의',
        '고양이', '강아지', '펫', '반려동물',
        '게임', '앱', '어플'
    ],
    '생활용품': [
        '영어', '일본어', '중국어', '학원', '교육', '과외', '강의',
        '게임', '앱', '어플',
        '부동산', '아파트', '오피스텔'
    ],
    '건강기능식품': [
        '영어', '일본어', '중국어', '학원', '교육', '과외', '강의',
        '고양이', '강아지', '펫', '반려동물',
        '게임', '앱', '어플',
        '피부관리', '리프팅', '디바이스', '미용기기'
    ],
    '뷰티디바이스': [
        '영어', '일본어', '중국어', '학원', '교육', '과외', '강의',
        '고양이', '강아지', '펫', '반려동물',
        '게임', '앱', '어플',
        '샴푸', '탈모샴푸', '두피샴푸', '트리트먼트',
        '금연', '담배', '흡연', '니코틴', '전자담배',
        '작곡', '음악', '믹싱', 'composer', 'music store'
    ]
}

# 카테고리별 필수 포함 키워드 (광고주명 또는 광고 텍스트에 하나라도 포함되어야 함)
INCLUDE_KEYWORDS = {
    '스킨케어': [
        '피부', '스킨', '얼굴', '크림', '로션', '앰플', '세럼', '토너', '에센스', '마스크', '팩',
        '미백', '주름', '탄력', '보습', '수분', '클렌징', '세안', '화장품', 'skincare', 'skin',
        '아이크림', '선크림', '자외선', 'UV', '안티에이징', '리프팅', '탄력', '모공', '각질',
        '여드름', '트러블', '진정', '수딩', '히알루론산', '콜라겐', '펩타이드', '레티놀',
        '나이아신아마이드', '비타민C', '센텔라', '알로에', '티트리'
    ],
    '헤어케어': [
        '모발', '헤어', '머리', '샴푸', '린스', '트리트먼트', '헤어팩', '두피', '탈모',
        '모발성장', '볼륨', '지루성', '염색', '펌', '헤어에센스', '헤어오일', '헤어앰플',
        '탈모샴푸', '두피샴푸', '헤어케어', 'hair', '아이롱', '고데기', '드라이기'
    ],
    '생활용품': [
        '베개', '이불', '침구', '매트리스', '쿠션', '방석',
        '세제', '세탁', '청소', '탈취', '방향', '습기제거', '곰팡이제거',
        '주방', '욕실', '화장실', '청소용품', '수납', '정리',
        '생활용품', '일상', '홈', '가정', '집'
    ],
    '건강기능식품': [
        '영양제', '건강', '다이어트', '체중', '감량', '보조제',
        '글루타치온', '오메가3', '비타민', '프로바이오틱스', '유산균', '칼슘',
        '마그네슘', '아연', '철분', '콜라겐', '히알루론산', '루테인',
        '밀크씨슬', '간', '면역', '혈행', '혈당', '혈압', '뼈', '관절',
        '먹는', '섭취', '복용', '캡슐', '정', '환', '분말', '건강기능식품'
    ],
    '뷰티디바이스': [
        '뷰티디바이스', '뷰티기기', '미용기기', '피부관리기기', '피부관리', '피부케어', '홈케어',
        '리프팅', '모공', 'LED', '갈바닉', '마사지', '고주파', '초음파', 'EMS', 'RF',
        '클렌징기기', '클렌징디바이스', '더마', '미용', '뷰티', '얼굴', '피부',
        '부스터', '메디큐브', '에이지알', '플라즈마', '브이쎄라', '쎄라',
        '홈뷰티', '셀프케어', '페이셜', '스킨케어기기'
    ]
}

def is_relevant_ad(ad, category):
    """광고가 카테고리에 적합한지 검사"""
    advertiser = ad.get('advertiser', '').lower()
    ad_text = ad.get('ad_text', '').lower()
    combined_text = advertiser + ' ' + ad_text
    
    # 뷰티디바이스 특별 규칙: 금연/담배 관련 강력 제외
    if category == '뷰티디바이스':
        smoking_keywords = ['금연', '담배', '흡연', '니코틴', '전자담배', '노담']
        for keyword in smoking_keywords:
            if keyword in combined_text:
                return False, f"금연/담배 관련 '{keyword}' 포함"
    
    # 1. 제외 키워드 체크
    exclude_words = EXCLUDE_KEYWORDS.get(category, [])
    for keyword in exclude_words:
        if keyword.lower() in combined_text:
            return False, f"제외 키워드 '{keyword}' 포함"
    
    # 2. 필수 포함 키워드 체크
    include_words = INCLUDE_KEYWORDS.get(category, [])
    if include_words:
        found_match = False
        for keyword in include_words:
            if keyword.lower() in combined_text:
                found_match = True
                break
        
        if not found_match:
            return False, "필수 키워드 미포함"
    
    return True, "적합"

def filter_data(input_file, output_file):
    """데이터 필터링"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stats = {
        'before': {},
        'after': {},
        'removed': {}
    }
    
    # 각 카테고리별로 필터링
    for category, cat_data in data['results'].items():
        total_before = 0
        total_after = 0
        removed_examples = []
        
        for query, result in cat_data['results_by_query'].items():
            ads = result.get('ads', [])
            total_before += len(ads)
            
            filtered_ads = []
            for ad in ads:
                is_valid, reason = is_relevant_ad(ad, category)
                if is_valid:
                    filtered_ads.append(ad)
                else:
                    if len(removed_examples) < 5:  # 처음 5개만 기록
                        removed_examples.append({
                            'advertiser': ad.get('advertiser'),
                            'text': ad.get('ad_text', '')[:100],
                            'reason': reason
                        })
            
            result['ads'] = filtered_ads
            result['total_ads'] = len(filtered_ads)
            result['unique_ads'] = len(filtered_ads)
            total_after += len(filtered_ads)
        
        cat_data['total_ads'] = total_after
        
        stats['before'][category] = total_before
        stats['after'][category] = total_after
        stats['removed'][category] = {
            'count': total_before - total_after,
            'examples': removed_examples
        }
    
    # 필터링된 데이터 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    print('=== 필터링 결과 ===\n')
    total_removed = 0
    for category in stats['before'].keys():
        before = stats['before'][category]
        after = stats['after'][category]
        removed = before - after
        total_removed += removed
        
        print(f'[{category}]')
        print(f'  필터링 전: {before}개')
        print(f'  필터링 후: {after}개')
        print(f'  제거됨: {removed}개 ({removed/before*100:.1f}%)')
        
        if stats['removed'][category]['examples']:
            print(f'  제거 예시:')
            for ex in stats['removed'][category]['examples']:
                print(f'    - {ex["advertiser"]}: {ex["text"]}... ({ex["reason"]})')
        print()
    
    print(f'전체 제거: {total_removed}개 광고')
    print(f'\n필터링된 데이터 저장: {output_file}')

if __name__ == '__main__':
    input_file = 'meta_output/meta_all_categories_20260211_190018.json'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'meta_output/meta_all_categories_filtered_{timestamp}.json'
    
    filter_data(input_file, output_file)
