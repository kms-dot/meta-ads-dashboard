"""
Meta 광고 레퍼런스 Streamlit 대시보드
URL로 접속 가능한 전사 배포용 대시보드
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="Meta 광고 레퍼런스 대시보드",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .ad-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .ad-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .top-performer {
        border: 3px solid #28a745;
        background: #f0fff4;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 함수
@st.cache_data(ttl=3600)  # 1시간 캐시
def load_latest_data():
    """최신 크롤링 결과 로드 (필터링된 데이터 우선)"""
    output_dir = Path("meta_output")

    if not output_dir.exists():
        return None

    # 1순위: 필터링된 파일 찾기
    filtered_files = list(output_dir.glob("meta_all_categories_filtered_*.json"))
    if filtered_files:
        latest_file = max(filtered_files, key=lambda x: x.stat().st_mtime)
    else:
        # 2순위: 일반 파일
        all_files = list(output_dir.glob("meta_all_categories_*.json"))
        if not all_files:
            return None
        latest_file = max(all_files, key=lambda x: x.stat().st_mtime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

# 이미지 URL 고화질 변환
def get_high_quality_image_url(url):
    """썸네일 URL을 고화질 이미지 URL로 변환"""
    if not url:
        return url
    
    # Facebook 이미지 URL 패턴 변환
    # s60x60 -> s600x600 (10배 크기)
    # dst-jpg_s60x60 -> dst-jpg_s600x600
    url = url.replace('_s60x60', '_s600x600')
    url = url.replace('s60x60', 's600x600')
    
    return url

# 광고 데이터 변환
def get_all_ads_from_category(cat_data):
    """카테고리 데이터에서 모든 광고 추출"""
    all_ads = []
    results_by_query = cat_data.get('results_by_query', {})

    for query, query_result in results_by_query.items():
        ads = query_result.get('ads', [])
        all_ads.extend(ads)

    return all_ads

# 메인 대시보드
def main():
    st.markdown('<div class="main-header">🎯 Meta 광고 레퍼런스 대시보드</div>', unsafe_allow_html=True)
    st.markdown("##### 성과형 광고 분석 - 장기 게재 & 고성과 광고")

    # 데이터 로드
    data = load_latest_data()

    if data is None:
        st.error("⚠️ 크롤링 데이터를 찾을 수 없습니다. meta_output/ 폴더를 확인해주세요.")
        return

    results = data['results']

    # 전체 통계 계산
    total_ads = sum(cat['total_ads'] for cat in results.values())
    total_advertisers = sum(
        cat.get('overall_analysis', {}).get('summary', {}).get('unique_advertisers', 0)
        for cat in results.values()
    )

    # 상단 메트릭
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 총 광고 수", f"{total_ads:,}개")

    with col2:
        st.metric("📁 카테고리", f"{len(results)}개")

    with col3:
        st.metric("👥 고유 광고주", f"{total_advertisers:,}개")

    with col4:
        crawl_date = data.get('crawl_date', '')
        if crawl_date:
            crawl_time = datetime.fromisoformat(crawl_date).strftime('%Y-%m-%d %H:%M')
            st.metric("🕐 최종 업데이트", crawl_time)

    st.markdown("---")

    # 사이드바: 카테고리 선택
    st.sidebar.title("⚙️ 필터 설정")

    selected_category = st.sidebar.selectbox(
        "카테고리 선택",
        options=list(results.keys()),
        index=0
    )

    # 장기 게재 필터
    min_days_filter = st.sidebar.slider(
        "최소 게재 일수",
        min_value=0,
        max_value=365,
        value=30,
        step=10,
        help="지정한 일수 이상 게재된 광고만 표시"
    )

    # 페이지당 광고 수
    ads_per_page = st.sidebar.selectbox(
        "페이지당 광고 수",
        options=[20, 50, 100, 200, 500],
        index=2
    )

    # 정렬 기준
    sort_by = st.sidebar.selectbox(
        "정렬 기준",
        options=["게재 기간 (긴 순)", "게재 기간 (짧은 순)", "최근 게재일"],
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.info("💡 광고 카드를 클릭하면 Meta 광고 라이브러리로 이동합니다.")

    # 선택된 카테고리 데이터
    cat_data = results[selected_category]

    # 카테고리 통계
    st.header(f"📊 {selected_category}")

    col1, col2, col3, col4 = st.columns(4)

    analysis = cat_data.get('overall_analysis', {})
    summary = analysis.get('summary', {})

    with col1:
        st.metric("광고 수", f"{cat_data['total_ads']:,}개")

    with col2:
        st.metric("고유 광고주", f"{summary.get('unique_advertisers', 0):,}개")

    with col3:
        st.metric("평균 라이브", f"{summary.get('avg_days_live', 0):.1f}일")

    with col4:
        target = 200
        achievement = (cat_data['total_ads'] / target) * 100
        st.metric("목표 달성률", f"{achievement:.0f}%")

    # 광고 데이터 가져오기
    all_ads = get_all_ads_from_category(cat_data)

    # 필터링: 최소 게재 일수
    filtered_ads = [
        ad for ad in all_ads
        if ad.get('days_live', 0) >= min_days_filter
    ]

    # 정렬
    if sort_by == "게재 기간 (긴 순)":
        filtered_ads.sort(key=lambda x: x.get('days_live', 0), reverse=True)
    elif sort_by == "게재 기간 (짧은 순)":
        filtered_ads.sort(key=lambda x: x.get('days_live', 0))
    elif sort_by == "최근 게재일":
        filtered_ads.sort(key=lambda x: x.get('start_date', ''), reverse=True)

    st.markdown(f"#### 필터링된 광고: {len(filtered_ads):,}개")

    # 페이지네이션
    total_pages = (len(filtered_ads) - 1) // ads_per_page + 1 if filtered_ads else 0

    if total_pages > 0:
        page = st.selectbox(
            f"페이지 선택 (총 {total_pages}페이지)",
            options=range(1, total_pages + 1),
            format_func=lambda x: f"페이지 {x}/{total_pages}"
        )

        start_idx = (page - 1) * ads_per_page
        end_idx = start_idx + ads_per_page
        page_ads = filtered_ads[start_idx:end_idx]

        st.markdown(f"현재 페이지: **{start_idx + 1} - {min(end_idx, len(filtered_ads))}** / {len(filtered_ads)}개")

        # 광고 표시 - 그리드 레이아웃 (4열)
        cols_per_row = 4
        for i in range(0, len(page_ads), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for col_idx, ad in enumerate(page_ads[i:i+cols_per_row]):
                advertiser = ad.get('advertiser', '광고주 정보 없음')
                ad_text = ad.get('ad_text', '광고 내용 없음')
                days_live = ad.get('days_live', 0)
                impression_text = ad.get('impression_text', '정보 없음')
                start_date = ad.get('start_date', '알 수 없음')
                ad_url = ad.get('ad_library_url', '#')
                
                # 이미지 우선순위: ad_creative_image_url > video_poster_url > thumbnail_url
                creative_url = ad.get('ad_creative_image_url', '')
                video_poster_url = ad.get('video_poster_url', '')
                thumb_url = ad.get('thumbnail_url', '')
                
                # 1순위: ad_creative_image_url (보통 s600x600 이미 포함)
                if creative_url:
                    image_url = creative_url
                # 2순위: 비디오 포스터 이미지
                elif video_poster_url:
                    image_url = get_high_quality_image_url(video_poster_url)
                # 3순위: thumbnail_url을 고화질로 변환
                elif thumb_url:
                    image_url = get_high_quality_image_url(thumb_url)
                else:
                    image_url = None
                
                is_top_performer = days_live >= 60
                
                with cols[col_idx]:
                    card_class = 'ad-card top-performer' if is_top_performer else 'ad-card'
                    st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
                    
                    # 장기 게재 배지
                    if is_top_performer:
                        st.markdown("🏆 **장기 게재 (60일+)**", unsafe_allow_html=True)
                    
                    # 썸네일 (고화질)
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        # 이미지 없을 때 광고주 전체 이름 표시
                        display_name = advertiser if advertiser else "광고주 정보 없음"
                        # 이름이 너무 길면 폰트 크기 조정
                        font_size = "2.5rem" if len(display_name) > 10 else "3rem" if len(display_name) > 6 else "3.5rem"
                        
                        st.markdown(f"""
                        <div style="
                            width: 100%;
                            aspect-ratio: 1;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            border-radius: 8px;
                            color: white;
                            font-size: {font_size};
                            font-weight: bold;
                            padding: 1rem;
                            text-align: center;
                            word-break: keep-all;
                            line-height: 1.3;
                        ">
                            {display_name}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 광고주명
                    st.markdown(f"**{advertiser}**")
                    
                    # 광고 텍스트 (짧게)
                    short_text = ad_text[:80] + "..." if len(ad_text) > 80 else ad_text
                    st.markdown(f"{short_text}")
                    
                    # 통계
                    st.markdown(f"📅 **{days_live}일 게재**")
                    st.markdown(f"👁️ {impression_text}")
                    st.markdown(f"🗓️ {start_date}")
                    
                    # 링크
                    if ad_url and ad_url != '#':
                        st.markdown(f"[광고 라이브러리에서 보기 →]({ad_url})")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("필터 조건에 맞는 광고가 없습니다.")

    # 하단: 상위 광고주
    st.markdown("---")
    st.header("🏆 상위 광고주 TOP 10")

    advertiser_stats = analysis.get('advertiser_stats', [])[:10]

    if advertiser_stats:
        df_advertisers = pd.DataFrame(advertiser_stats)

        fig = px.bar(
            df_advertisers,
            x='ad_count',
            y='advertiser',
            orientation='h',
            title="광고주별 광고 수",
            labels={'ad_count': '광고 수', 'advertiser': '광고주'},
            color='ad_count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
