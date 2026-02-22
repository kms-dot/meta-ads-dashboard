import streamlit as st
import json
import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import threading
import subprocess
import sys

# 페이지 설정
st.set_page_config(
    page_title="Meta 광고 크롤링 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
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
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-text {
        color: #28a745;
        font-weight: bold;
    }
    .warning-text {
        color: #ffc107;
        font-weight: bold;
    }
    .error-text {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="main-header">📊 Meta 광고 크롤링 실시간 대시보드</div>', unsafe_allow_html=True)

# 사이드바
st.sidebar.title("⚙️ 설정")
auto_refresh = st.sidebar.checkbox("자동 새로고침", value=True)
refresh_interval = st.sidebar.slider("새로고침 간격 (초)", 1, 10, 3)

# 크롤링 실행 버튼
if st.sidebar.button("🚀 크롤링 시작", type="primary"):
    with st.spinner("크롤링을 시작합니다..."):
        # 백그라운드에서 크롤링 실행
        subprocess.Popen([sys.executable, "main_meta.py"],
                        cwd=os.getcwd(),
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        st.sidebar.success("✅ 크롤링이 시작되었습니다!")
        time.sleep(1)

st.sidebar.markdown("---")
st.sidebar.info("💡 대시보드는 자동으로 최신 결과를 표시합니다.")

# 데이터 로드 함수
@st.cache_data(ttl=refresh_interval)
def load_latest_results():
    """최신 크롤링 결과 로드"""
    output_dir = Path("meta_output")

    if not output_dir.exists():
        return None, None, []

    # 전체 결과 파일 찾기
    all_categories_files = list(output_dir.glob("meta_all_categories_*.json"))

    if not all_categories_files:
        return None, None, []

    # 가장 최신 파일
    latest_file = max(all_categories_files, key=lambda x: x.stat().st_mtime)

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 개별 키워드 파일들
        keyword_files = list(output_dir.glob("meta_*.json"))
        keyword_files = [f for f in keyword_files if "all_categories" not in f.name and "summary" not in f.name]
        keyword_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return data, latest_file, keyword_files[:20]  # 최근 20개만
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None, None, []

def load_log_file():
    """최신 로그 파일 로드"""
    output_dir = Path("meta_output")
    if not output_dir.exists():
        return []

    log_files = list(output_dir.glob("meta_crawl_*.log"))
    if not log_files:
        return []

    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-50:]  # 최근 50줄
    except:
        return []

# 메인 대시보드
data, latest_file, keyword_files = load_latest_results()

if data is None:
    st.warning("⏳ 크롤링 결과를 기다리는 중...")
    st.info("'크롤링 시작' 버튼을 눌러 크롤링을 시작하세요.")

    # 로그 표시
    st.subheader("📝 실시간 로그")
    log_lines = load_log_file()
    if log_lines:
        log_text = "".join(log_lines)
        st.text_area("크롤링 로그", log_text, height=300)

    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

    st.stop()

# 결과 표시
st.success(f"✅ 최신 결과: {latest_file.name} (수정 시간: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})")

# 전체 통계
col1, col2, col3, col4 = st.columns(4)

total_ads = sum(cat_data['total_ads'] for cat_data in data['results'].values())
total_categories = len(data['results'])
total_advertisers = sum(
    cat_data.get('overall_analysis', {}).get('summary', {}).get('unique_advertisers', 0)
    for cat_data in data['results'].values()
)

with col1:
    st.metric("📊 총 광고 수", f"{total_ads:,}개")

with col2:
    st.metric("📁 카테고리 수", f"{total_categories}개")

with col3:
    st.metric("👥 고유 광고주", f"{total_advertisers:,}개")

with col4:
    crawl_date = data.get('crawl_date', '')
    if crawl_date:
        crawl_time = datetime.fromisoformat(crawl_date).strftime('%H:%M:%S')
        st.metric("🕐 크롤링 시간", crawl_time)

st.markdown("---")

# 카테고리별 탭
tab_names = list(data['results'].keys())
tabs = st.tabs([f"📊 {name}" for name in tab_names])

for idx, (cat_name, tab) in enumerate(zip(tab_names, tabs)):
    cat_data = data['results'][cat_name]

    with tab:
        # 카테고리 요약
        col1, col2, col3, col4 = st.columns(4)

        analysis = cat_data.get('overall_analysis', {})
        summary = analysis.get('summary', {})

        with col1:
            st.metric("광고 수", f"{cat_data['total_ads']:,}개")

        with col2:
            unique_advertisers = summary.get('unique_advertisers', 0)
            st.metric("고유 광고주", f"{unique_advertisers:,}개")

        with col3:
            avg_days = summary.get('avg_days_live', 0)
            st.metric("평균 라이브", f"{avg_days:.1f}일")

        with col4:
            results_by_query = cat_data.get('results_by_query', {})
            success_queries = len([q for q in results_by_query.values() if q.get('unique_ads', 0) > 0])
            st.metric("성공 키워드", f"{success_queries}개")

        # 목표 달성률
        target = 200
        achievement = (cat_data['total_ads'] / target) * 100

        if achievement >= 100:
            st.markdown(f"<div class='success-text'>✅ 목표 달성: {achievement:.0f}% ({cat_data['total_ads']}/{target}개)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='warning-text'>⚠️ 목표 진행 중: {achievement:.0f}% ({cat_data['total_ads']}/{target}개)</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 상위 광고주
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏆 상위 광고주 TOP 10")
            advertiser_stats = analysis.get('advertiser_stats', [])[:10]

            if advertiser_stats:
                df_advertisers = pd.DataFrame(advertiser_stats)

                # 막대 차트
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

                # 테이블
                df_advertisers['순위'] = range(1, len(df_advertisers) + 1)
                df_display = df_advertisers[['순위', 'advertiser', 'ad_count']].rename(columns={
                    'advertiser': '광고주',
                    'ad_count': '광고 수'
                })
                st.dataframe(df_display, hide_index=True, use_container_width=True)

        with col2:
            st.subheader("📈 키워드별 수집 현황")

            # 키워드별 데이터
            keyword_data = []
            for query, query_result in results_by_query.items():
                keyword_data.append({
                    '키워드': query,
                    '수집': query_result.get('total_ads', 0),
                    '고유': query_result.get('unique_ads', 0),
                    '소요시간': f"{query_result.get('elapsed_seconds', 0):.0f}초"
                })

            if keyword_data:
                df_keywords = pd.DataFrame(keyword_data)
                df_keywords = df_keywords.sort_values('고유', ascending=False)

                # 파이 차트
                fig = px.pie(
                    df_keywords.head(10),
                    values='고유',
                    names='키워드',
                    title="키워드별 광고 분포 (TOP 10)",
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # 테이블
                st.dataframe(df_keywords, hide_index=True, use_container_width=True)

# 전체 비교
st.markdown("---")
st.subheader("📊 카테고리 비교")

col1, col2 = st.columns(2)

with col1:
    # 카테고리별 광고 수 비교
    category_comparison = []
    for cat_name, cat_data in data['results'].items():
        category_comparison.append({
            '카테고리': cat_name,
            '광고 수': cat_data['total_ads'],
            '광고주 수': cat_data.get('overall_analysis', {}).get('summary', {}).get('unique_advertisers', 0)
        })

    df_comparison = pd.DataFrame(category_comparison)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='광고 수',
        x=df_comparison['카테고리'],
        y=df_comparison['광고 수'],
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        name='광고주 수',
        x=df_comparison['카테고리'],
        y=df_comparison['광고주 수'],
        marker_color='#ff7f0e'
    ))

    fig.update_layout(
        title="카테고리별 광고 수 vs 광고주 수",
        barmode='group',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # 평균 라이브 일수 비교
    live_days_data = []
    for cat_name, cat_data in data['results'].items():
        avg_days = cat_data.get('overall_analysis', {}).get('summary', {}).get('avg_days_live', 0)
        live_days_data.append({
            '카테고리': cat_name,
            '평균 라이브': avg_days
        })

    df_live = pd.DataFrame(live_days_data)

    fig = px.bar(
        df_live,
        x='카테고리',
        y='평균 라이브',
        title="카테고리별 평균 광고 라이브 일수",
        color='평균 라이브',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# 최근 키워드 파일 목록
st.markdown("---")
st.subheader("📂 최근 수집된 키워드")

if keyword_files:
    keyword_info = []
    for kf in keyword_files:
        try:
            with open(kf, 'r', encoding='utf-8') as f:
                kf_data = json.load(f)
                keyword_info.append({
                    '파일명': kf.name,
                    '키워드': kf_data.get('query', 'N/A'),
                    '광고 수': kf_data.get('total_ads', 0),
                    '고유 광고': kf_data.get('unique_ads', 0),
                    '수정 시간': datetime.fromtimestamp(kf.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        except:
            continue

    if keyword_info:
        df_files = pd.DataFrame(keyword_info)
        st.dataframe(df_files, hide_index=True, use_container_width=True)

# 실시간 로그
with st.expander("📝 실시간 크롤링 로그", expanded=False):
    log_lines = load_log_file()
    if log_lines:
        log_text = "".join(log_lines)
        st.text_area("로그", log_text, height=300, label_visibility="collapsed")
    else:
        st.info("로그 파일이 없습니다.")

# 푸터
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🔄 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    st.caption(f"📁 출력 디렉토리: meta_output/")
with col3:
    if auto_refresh:
        st.caption(f"⏱️ {refresh_interval}초 후 자동 새로고침")

# 자동 새로고침
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
