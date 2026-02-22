"""
Meta 광고 레퍼런스 Streamlit 대시보드 v2
탭 1: Meta 광고 (기존) | 탭 2: 성과 광고 TOP (신규) | 탭 3: 바이럴 컨텐츠 (신규)

변경 이력
---------
v2  - Instagram 성과 데이터 통합
    - CTA 감지 로직
    - 바이럴 점수 계산 (views*1 + likes*10 + comments*50) / days_since_posted
    - 3탭 구조로 리뉴얼
"""

import streamlit as st
import json
import re
import os
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta, date

# ─────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Meta 광고 레퍼런스 대시보드 v2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────
st.markdown("""
<style>
  .main-header {
    font-size: 2.1rem; font-weight: 800;
    color: #1f77b4; text-align: center; margin-bottom: 0.3rem;
  }
  .version-badge {
    display: inline-block; background: #764ba2; color: white;
    font-size: 0.7rem; font-weight: bold;
    padding: 2px 10px; border-radius: 12px;
    margin-left: 8px; vertical-align: middle;
  }
  .ad-card {
    border: 2px solid #e0e0e0; border-radius: 12px;
    padding: 0.85rem; margin: 0.3rem 0;
    background: #ffffff; transition: all 0.2s;
  }
  .ad-card:hover {
    border-color: #667eea;
    box-shadow: 0 4px 16px rgba(102,126,234,0.22);
    transform: translateY(-2px);
  }
  .top-performer { border: 3px solid #28a745; background: #f0fff4; }
  .cta-badge {
    display: inline-block; background: #ff6b35; color: white;
    font-size: 0.68rem; font-weight: bold;
    padding: 1px 8px; border-radius: 8px; margin-right: 4px;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  .viral-badge {
    display: inline-block;
    background: linear-gradient(90deg, #f093fb, #f5576c);
    color: white; font-size: 0.68rem; font-weight: bold;
    padding: 1px 8px; border-radius: 8px;
  }
  .metric-row { font-size: 0.8rem; color: #444; margin: 2px 0; }
  .category-tag {
    display: inline-block; background: #e8f0fe; color: #1a73e8;
    font-size: 0.65rem; padding: 2px 7px;
    border-radius: 6px; margin: 2px 1px;
  }
  .no-data-box {
    background: #f8f9fa; border: 2px dashed #dee2e6;
    border-radius: 12px; padding: 2.5rem; text-align: center; color: #6c757d;
  }
  div[data-testid="stMetricValue"] { font-size: 1.35rem !important; }
  .stTabs [data-baseweb="tab"] {
    font-size: 1rem; font-weight: 600; padding: 10px 24px;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# 데이터 로드: Meta 광고 JSON
# ─────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_meta_data():
    """최신 Meta 광고 크롤링 결과 로드 (필터링 파일 우선)"""
    output_dir = Path("meta_output")
    if not output_dir.exists():
        return None
    filtered = list(output_dir.glob("meta_all_categories_filtered_*.json"))
    all_files = list(output_dir.glob("meta_all_categories_*.json"))
    files = filtered if filtered else all_files
    if not files:
        return None
    latest = max(files, key=lambda x: x.stat().st_mtime)
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────
# 데이터 로드: Instagram 성과 데이터 JSON
# ─────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_instagram_data() -> dict:
    """meta_output/instagram_data.json 로드 → {ad_library_url: {...}} dict"""
    ig_path = Path("meta_output/instagram_data.json")
    if not ig_path.exists():
        return {}
    with open(ig_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw.get("data", {})


# ─────────────────────────────────────────────────
# 데이터 로드: Instagram 해시태그 바이럴 포스트
# ─────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_viral_posts() -> list:
    """meta_output/viral_posts.json 로드 → post dict 리스트"""
    vp_path = Path("meta_output/viral_posts.json")
    if not vp_path.exists():
        return []
    try:
        with open(vp_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw.get("posts", [])
    except Exception:
        return []


# ─────────────────────────────────────────────────
# CTA 감지 로직
# ─────────────────────────────────────────────────
_CTA_KEYWORDS = [
    "프로필 링크", "링크는 프로필", "바이오 링크", "링크 클릭",
    "자세한 내용은", "구매는", "구매하기", "지금 구매", "지금 바로",
    "신청하기", "예약하기", "무료 체험", "무료 상담",
    "홈페이지", "웹사이트", "바로가기", "공식 홈", "스토어",
    "클릭하세요", "확인하세요", "쇼핑하기", "장바구니",
]

def detect_cta(caption_text: str) -> bool:
    """캡션 텍스트에서 CTA 여부 판단"""
    if not caption_text:
        return False
    # URL 포함 여부
    if re.search(r"https?://", caption_text):
        return True
    text_lower = caption_text.lower()
    return any(kw.lower() in text_lower for kw in _CTA_KEYWORDS)


# ─────────────────────────────────────────────────
# 바이럴 점수 계산
# ─────────────────────────────────────────────────
def calc_viral_score(views: int, likes: int, comments: int,
                     shares: int = 0,
                     post_date_str: str = "") -> float:
    """viral_score = views×1 + likes×10 + comments×50 + shares×100
    ※ 게시 날짜는 점수 계산에 미사용 (화면 "N일 전" 표기용만)
    """
    return float(views * 1 + likes * 10 + comments * 50 + shares * 100)


def days_ago_label(post_date_str: str) -> str:
    try:
        post_dt = datetime.strptime(post_date_str, "%Y-%m-%d").date()
        d = (date.today() - post_dt).days
        return "오늘" if d == 0 else f"{d}일 전"
    except Exception:
        return "날짜 불명"


# ─────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────
def get_hq_image(url: str) -> str:
    """썸네일 URL을 고화질로 변환"""
    if not url:
        return url
    url = url.replace("_s60x60", "_s600x600")
    url = url.replace("s60x60", "s600x600")
    return url


def get_best_image(ad: dict):
    creative = ad.get("ad_creative_image_url", "")
    poster   = ad.get("video_poster_url", "")
    thumb    = ad.get("thumbnail_url", "")
    if creative: return creative
    if poster:   return get_hq_image(poster)
    if thumb:    return get_hq_image(thumb)
    return None


def fmt_num(n: int) -> str:
    """숫자를 K / M 단위로 포맷"""
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)


def get_all_ads_from_category(cat_data: dict) -> list:
    ads = []
    for q_result in cat_data.get("results_by_query", {}).values():
        ads.extend(q_result.get("ads", []))
    return ads


def merge_all_ads(meta_data: dict, ig_data: dict) -> list:
    """전 카테고리 광고를 flat list 로, Instagram 데이터 병합"""
    merged = []
    for cat_name, cat_data in meta_data.get("results", {}).items():
        for ad in get_all_ads_from_category(cat_data):
            ad = dict(ad)                          # 원본 변경 방지
            ad["_category"] = cat_name
            url = ad.get("ad_library_url", "")
            ig  = ig_data.get(url, {})
            ad["instagram_url"]      = ig.get("instagram_url", "")
            ad["instagram_views"]    = ig.get("instagram_views", 0)
            ad["instagram_likes"]    = ig.get("instagram_likes", 0)
            ad["instagram_comments"] = ig.get("instagram_comments", 0)
            ad["post_date"]          = ig.get("post_date", "")
            ad["has_cta"]            = ig.get("has_cta", False)
            ad["viral_score"]        = ig.get("viral_score", 0.0)
            ad["caption_text"]       = ig.get("caption_text", "")
            merged.append(ad)
    return merged


# ─────────────────────────────────────────────────
# 광고 카드 렌더 (탭 공통)
# ─────────────────────────────────────────────────
def render_ad_card(ad: dict, col,
                   show_ig: bool = False,
                   show_viral: bool = False):
    """광고 1장을 카드 형식으로 렌더링"""
    advertiser = ad.get("advertiser", "광고주 정보 없음")
    ad_text    = ad.get("ad_text", "")
    days_live  = ad.get("days_live", 0)
    ad_url     = ad.get("ad_library_url", "#")
    ig_url     = ad.get("instagram_url", "")
    views      = ad.get("instagram_views", 0)
    likes      = ad.get("instagram_likes", 0)
    comments   = ad.get("instagram_comments", 0)
    has_cta    = ad.get("has_cta", False)
    viral      = ad.get("viral_score", 0.0)
    post_date  = ad.get("post_date", "")
    category   = ad.get("_category", "")
    image_url  = get_best_image(ad)
    is_top     = days_live >= 60

    with col:
        # ── 배지 ──
        badges = ""
        if has_cta:
            badges += '<span class="cta-badge">🔗 CTA</span> '
        if show_viral and viral > 0:
            badges += f'<span class="viral-badge">🔥 {viral:,.0f}점</span>'
        if is_top and not show_ig:
            badges += ' <span style="color:#28a745;font-size:0.7rem;">🏆 장기게재</span>'
        if badges:
            st.markdown(badges, unsafe_allow_html=True)

        # ── 썸네일 ──
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            fs = "2rem" if len(advertiser) > 10 else "2.6rem"
            st.markdown(f"""
            <div style="width:100%;aspect-ratio:1;
              background:linear-gradient(135deg,#667eea,#764ba2);
              display:flex;align-items:center;justify-content:center;
              border-radius:8px;color:white;font-size:{fs};
              font-weight:bold;text-align:center;padding:0.8rem;">
              {advertiser}
            </div>""", unsafe_allow_html=True)

        # ── 브랜드명 + 카테고리 태그 ──
        st.markdown(f"**{advertiser}**")
        if category:
            st.markdown(
                f'<span class="category-tag">{category}</span>',
                unsafe_allow_html=True
            )

        # ── 광고 텍스트 ──
        if ad_text:
            short = ad_text[:70] + "…" if len(ad_text) > 70 else ad_text
            st.caption(short)

        # ── Meta 지표 ──
        st.markdown(
            f'<div class="metric-row">📅 <b>{days_live}일</b> 게재</div>',
            unsafe_allow_html=True
        )

        # ── Instagram 지표 ──
        if show_ig and (views or likes or comments):
            st.markdown(
                f'<div class="metric-row">'
                f'👁️ {fmt_num(views)}&nbsp;&nbsp;'
                f'❤️ {fmt_num(likes)}&nbsp;&nbsp;'
                f'💬 {fmt_num(comments)}</div>',
                unsafe_allow_html=True
            )

        # ── 게시 날짜 ──
        if post_date:
            st.markdown(
                f'<div class="metric-row">🗓️ {days_ago_label(post_date)}</div>',
                unsafe_allow_html=True
            )

        # ── 링크 버튼 ──
        links = ""
        if ig_url:
            links += (f'<a href="{ig_url}" target="_blank" '
                      f'style="margin-right:8px;font-size:0.77rem;">📸 Instagram</a>')
        if ad_url and ad_url != "#":
            links += (f'<a href="{ad_url}" target="_blank" '
                      f'style="font-size:0.77rem;">📋 광고 라이브러리</a>')
        if links:
            st.markdown(links, unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# 바이럴 카드 렌더 (탭 3 전용)
# ─────────────────────────────────────────────────
def render_viral_card(post: dict, col):
    """Instagram 해시태그 바이럴 포스트 카드"""
    ig_url    = post.get("instagram_url", "#")
    thumb     = post.get("thumbnail_url", "")
    category  = post.get("category", "")
    hashtag   = post.get("hashtag", "")
    views     = post.get("instagram_views",    0)
    likes     = post.get("instagram_likes",    0)
    comments  = post.get("instagram_comments", 0)
    shares    = post.get("instagram_shares",   0)
    viral     = post.get("viral_score",        0.0)
    post_date = post.get("post_date",          "")
    caption   = post.get("caption_text",       "")
    is_reel   = post.get("is_reel",            False)

    with col:
        # ── 바이럴 점수 배지 (강조) ──
        reel_icon = "🎬" if is_reel else "📷"
        st.markdown(
            f'<div style="text-align:center;margin-bottom:4px;">'
            f'<span class="viral-badge">{reel_icon} '
            f'🔥 {viral:,.0f}점</span></div>',
            unsafe_allow_html=True
        )

        # ── 썸네일 ──
        if thumb:
            st.image(thumb, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="width:100%;aspect-ratio:1;
              background:linear-gradient(135deg,#f093fb,#f5576c);
              display:flex;align-items:center;justify-content:center;
              border-radius:8px;color:white;font-size:2.2rem;
              font-weight:bold;text-align:center;">
              {reel_icon}
            </div>""", unsafe_allow_html=True)

        # ── 카테고리 + 해시태그 ──
        st.markdown(
            f'<span class="category-tag">{category}</span>'
            f'<span class="category-tag">#{hashtag}</span>',
            unsafe_allow_html=True
        )

        # ── 성과 지표 (4개) ──
        st.markdown(
            f'<div class="metric-row">'
            f'👁️ <b>{fmt_num(views)}</b>&nbsp; '
            f'❤️ <b>{fmt_num(likes)}</b>&nbsp; '
            f'💬 <b>{fmt_num(comments)}</b>&nbsp; '
            f'📤 <b>{fmt_num(shares)}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── 게시 날짜 ("N일 전") ──
        if post_date:
            st.markdown(
                f'<div class="metric-row">🗓️ {days_ago_label(post_date)}</div>',
                unsafe_allow_html=True
            )

        # ── 캡션 미리보기 ──
        if caption:
            short = caption[:65] + "…" if len(caption) > 65 else caption
            st.caption(short)

        # ── Instagram 원본 링크 ──
        if ig_url and ig_url != "#":
            st.markdown(
                f'<a href="{ig_url}" target="_blank" '
                f'style="font-size:0.77rem;">📸 Instagram 원본 보기</a>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────
def main():
    st.markdown(
        '<div class="main-header">🎯 Meta 광고 레퍼런스 대시보드'
        '<span class="version-badge">v2</span></div>',
        unsafe_allow_html=True
    )
    st.caption("Meta 광고 라이브러리 + Instagram 성과 데이터 통합 분석")

    # 데이터 로드
    meta_data        = load_meta_data()
    ig_data          = load_instagram_data()
    viral_posts_data = load_viral_posts()        # 해시태그 바이럴 포스트

    if meta_data is None:
        st.error("⚠️ 크롤링 데이터를 찾을 수 없습니다. meta_output/ 폴더를 확인해주세요.")
        return

    results  = meta_data.get("results", {})
    all_cats = list(results.keys())
    all_ads  = merge_all_ads(meta_data, ig_data)

    # 글로벌 집계
    total_ads = sum(c["total_ads"] for c in results.values())
    total_adv = sum(
        c.get("overall_analysis", {}).get("summary", {}).get("unique_advertisers", 0)
        for c in results.values()
    )
    ig_synced     = sum(1 for a in all_ads if a.get("instagram_url"))
    ig_cta_count  = sum(1 for a in all_ads if a.get("has_cta"))
    crawl_str     = meta_data.get("crawl_date", "")
    crawl_label   = (
        datetime.fromisoformat(crawl_str).strftime("%m/%d %H:%M")
        if crawl_str else "—"
    )

    viral_count = len(viral_posts_data)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📊 총 Meta 광고",  f"{total_ads:,}개")
    m2.metric("📁 카테고리",      f"{len(results)}개")
    m3.metric("👥 광고주",        f"{total_adv:,}개")
    m4.metric("🔥 바이럴 포스트", f"{viral_count:,}개")
    m5.metric("🕐 업데이트",      crawl_label)

    st.markdown("---")

    # ─── 탭 생성 ───
    tab1, tab2, tab3 = st.tabs([
        "🎯  Meta 광고",
        "🔥  성과 광고 TOP",
        "📈  바이럴 컨텐츠",
    ])

    # ══════════════════════════════════════════════
    # 탭 1: Meta 광고 (기존 기능 동일 유지)
    # ══════════════════════════════════════════════
    with tab1:
        col_f1, col_m1 = st.columns([1, 4])

        with col_f1:
            st.markdown("### ⚙️ 필터")
            sel_cat1   = st.selectbox("카테고리", all_cats, key="t1_cat")
            min_days1  = st.slider("최소 게재 일수", 0, 365, 30, 10, key="t1_days")
            ads_pp1    = st.selectbox(
                "페이지당 광고 수", [20, 50, 100, 200], index=2, key="t1_pp"
            )
            sort1      = st.selectbox(
                "정렬 기준",
                ["게재 기간 (긴 순)", "게재 기간 (짧은 순)", "최근 게재일"],
                key="t1_sort"
            )
            st.markdown("---")
            st.info("💡 광고 카드 링크 클릭 시 Meta 광고 라이브러리로 이동합니다.")

        with col_m1:
            cat_data1 = results[sel_cat1]
            analysis1 = cat_data1.get("overall_analysis", {})
            summary1  = analysis1.get("summary", {})

            st.markdown(f"### 📊 {sel_cat1}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("광고 수",      f"{cat_data1['total_ads']:,}개")
            c2.metric("고유 광고주",  f"{summary1.get('unique_advertisers', 0):,}개")
            c3.metric("평균 라이브",  f"{summary1.get('avg_days_live', 0):.1f}일")
            target_rate = cat_data1["total_ads"] / 200 * 100
            c4.metric("목표 달성률", f"{target_rate:.0f}%")

            # 광고 추출 → 필터 → 정렬
            cat_ads1   = get_all_ads_from_category(cat_data1)
            filtered1  = [a for a in cat_ads1 if a.get("days_live", 0) >= min_days1]

            if sort1 == "게재 기간 (긴 순)":
                filtered1.sort(key=lambda x: x.get("days_live", 0), reverse=True)
            elif sort1 == "게재 기간 (짧은 순)":
                filtered1.sort(key=lambda x: x.get("days_live", 0))
            else:
                filtered1.sort(key=lambda x: x.get("start_date", ""), reverse=True)

            st.caption(f"필터링된 광고: **{len(filtered1):,}개**")

            # 페이지네이션
            total_p1 = max(1, (len(filtered1) - 1) // ads_pp1 + 1)
            page1 = st.selectbox(
                f"페이지 선택 (총 {total_p1}페이지)",
                range(1, total_p1 + 1),
                format_func=lambda x: f"페이지 {x}/{total_p1}",
                key="t1_page"
            )
            si1 = (page1 - 1) * ads_pp1
            ei1 = si1 + ads_pp1
            page_ads1 = filtered1[si1:ei1]
            st.caption(f"{si1+1} – {min(ei1, len(filtered1))} / {len(filtered1)}개")

            # 4열 그리드 렌더
            if page_ads1:
                for i in range(0, len(page_ads1), 4):
                    cols1 = st.columns(4)
                    for j, ad in enumerate(page_ads1[i:i+4]):
                        render_ad_card(ad, cols1[j], show_ig=False)
            else:
                st.warning("필터 조건에 맞는 광고가 없습니다.")

            # 상위 광고주 TOP 10 차트
            st.markdown("---")
            st.markdown("#### 🏆 상위 광고주 TOP 10")
            adv_stats1 = analysis1.get("advertiser_stats", [])[:10]
            if adv_stats1:
                df_adv = pd.DataFrame(adv_stats1)
                fig1 = px.bar(
                    df_adv,
                    x="ad_count", y="advertiser", orientation="h",
                    labels={"ad_count": "광고 수", "advertiser": "광고주"},
                    color="ad_count", color_continuous_scale="Blues",
                    title="광고주별 광고 수"
                )
                fig1.update_layout(height=380, showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)

    # ══════════════════════════════════════════════
    # 탭 2: 성과 광고 TOP — CTA 감지 광고
    # ══════════════════════════════════════════════
    with tab2:
        # Instagram 데이터 연동된 광고만
        ig_ads = [a for a in all_ads if a.get("instagram_url")]

        if not ig_ads:
            st.markdown("""
            <div class="no-data-box">
                <h3>📸 Instagram 데이터 수집 전</h3>
                <p>아직 Instagram 성과 데이터가 없습니다.<br>
                아래 명령어로 수집을 시작하세요:</p>
                <code>python instagram_updater.py</code>
                <p style="margin-top:1rem;font-size:0.85rem;color:#888">
                ⏰ 자동화: 매일 오전 3시 GitHub Actions가 자동 업데이트합니다.
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:
            col_f2, col_m2 = st.columns([1, 4])

            with col_f2:
                st.markdown("### ⚙️ 필터")
                st.success("✅ CTA 있는 광고만 표시")

                cat_opts2 = ["전체"] + all_cats
                sel_cat2  = st.selectbox("카테고리", cat_opts2, key="t2_cat")

                # 슬라이더 최대값: 실제 데이터 기준
                max_v2 = max((a.get("instagram_views",    0) for a in ig_ads), default=1)
                max_l2 = max((a.get("instagram_likes",    0) for a in ig_ads), default=1)
                max_c2 = max((a.get("instagram_comments", 0) for a in ig_ads), default=1)

                min_views2    = st.slider("최소 조회수",  0, max_v2, 0, max(max_v2//20, 1), key="t2_v")
                min_likes2    = st.slider("최소 좋아요",  0, max_l2, 0, max(max_l2//20, 1), key="t2_l")
                min_comments2 = st.slider("최소 댓글",    0, max_c2, 0, max(max_c2//20, 1), key="t2_c")

                sort2  = st.selectbox(
                    "정렬 기준", ["조회수 순", "좋아요 순", "댓글 순"], key="t2_sort"
                )
                ads_pp2 = st.selectbox(
                    "페이지당 광고 수", [12, 24, 48], index=0, key="t2_pp"
                )

            with col_m2:
                st.markdown("### 🔥 성과 광고 TOP — CTA 감지 광고")

                # 필터 적용 (has_cta 필수)
                t2 = [
                    a for a in ig_ads
                    if a.get("has_cta", False)
                    and a.get("instagram_views",    0) >= min_views2
                    and a.get("instagram_likes",    0) >= min_likes2
                    and a.get("instagram_comments", 0) >= min_comments2
                    and (sel_cat2 == "전체" or a.get("_category") == sel_cat2)
                ]

                # 정렬
                sort_key2 = {
                    "조회수 순": "instagram_views",
                    "좋아요 순": "instagram_likes",
                    "댓글 순":   "instagram_comments",
                }.get(sort2, "instagram_views")
                t2.sort(key=lambda x: x.get(sort_key2, 0), reverse=True)

                # 집계 메트릭
                avg_views2 = int(
                    sum(a.get("instagram_views", 0) for a in t2) / max(len(t2), 1)
                )
                c1, c2, c3 = st.columns(3)
                c1.metric("CTA 광고 수",  f"{len(t2):,}개")
                c2.metric("평균 조회수",   fmt_num(avg_views2))
                c3.metric("필터 카테고리", sel_cat2)

                if not t2:
                    st.warning("조건에 맞는 성과 광고가 없습니다. 슬라이더를 낮춰보세요.")
                else:
                    total_p2 = max(1, (len(t2) - 1) // ads_pp2 + 1)
                    page2 = st.selectbox(
                        f"페이지 선택 (총 {total_p2}페이지)",
                        range(1, total_p2 + 1),
                        format_func=lambda x: f"페이지 {x}/{total_p2}",
                        key="t2_page"
                    )
                    si2 = (page2 - 1) * ads_pp2
                    ei2 = si2 + ads_pp2
                    show2 = t2[si2:ei2]
                    st.caption(f"{si2+1} – {min(ei2, len(t2))} / {len(t2)}개")

                    for i in range(0, len(show2), 4):
                        cols2 = st.columns(4)
                        for j, ad in enumerate(show2[i:i+4]):
                            render_ad_card(ad, cols2[j], show_ig=True)

    # ══════════════════════════════════════════════
    # 탭 3: 바이럴 컨텐츠 (Instagram 해시태그 크롤)
    # ══════════════════════════════════════════════
    with tab3:
        if not viral_posts_data:
            st.markdown("""
            <div class="no-data-box">
                <h3>📈 바이럴 컨텐츠 수집 전</h3>
                <p>Instagram 해시태그 크롤링 데이터가 아직 없습니다.<br>
                아래 명령어로 수집을 시작하세요:</p>
                <code>python instagram_hashtag_crawler.py</code>
                <p style="margin-top:1rem;font-size:0.85rem;color:#888">
                ⏰ 자동화: 매일 오전 6시 GitHub Actions가 자동 수집합니다.<br>
                🔥 바이럴 점수 = 조회수×1 + 좋아요×10 + 댓글×50 + 공유×100
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            col_f3, col_m3 = st.columns([1, 4])

            with col_f3:
                st.markdown("### ⚙️ 필터")
                period3 = st.radio(
                    "기간 선택", ["최근 7일", "최근 30일", "전체"],
                    index=1, key="t3_period"
                )
                # 해시태그 크롤 6개 카테고리
                vp_cats   = sorted({
                    p.get("category", "") for p in viral_posts_data
                    if p.get("category")
                })
                cat_opts3 = ["전체"] + vp_cats
                sel_cat3  = st.selectbox("카테고리", cat_opts3, key="t3_cat")

                max_vs3 = max(
                    (p.get("viral_score", 0) for p in viral_posts_data), default=1
                )
                min_vs3 = st.slider(
                    "최소 바이럴 점수", 0, int(max_vs3), 0,
                    max(int(max_vs3) // 20, 1), key="t3_vs"
                )
                sort3   = st.selectbox(
                    "정렬 기준", ["바이럴 점수 순", "최신 순"], key="t3_sort"
                )
                ads_pp3 = st.selectbox(
                    "페이지당 포스트 수", [12, 24, 48], index=0, key="t3_pp"
                )
                st.markdown("---")
                st.caption(
                    "🔥 바이럴 점수 공식\n"
                    "= 조회수×1 + 좋아요×10\n"
                    "+ 댓글×50 + 공유×100\n"
                    "(게시일 미적용 — 날짜는 N일 전 표기용)"
                )

            with col_m3:
                st.markdown("### 📈 바이럴 컨텐츠 — Instagram 해시태그 크롤")

                # 기간 cutoff 계산
                if period3 == "최근 7일":
                    cutoff3 = (date.today() - timedelta(days=7)).isoformat()
                elif period3 == "최근 30일":
                    cutoff3 = (date.today() - timedelta(days=30)).isoformat()
                else:
                    cutoff3 = "2000-01-01"

                # 필터 적용 (viral_posts_data 사용)
                t3 = [
                    p for p in viral_posts_data
                    if (period3 == "전체"
                        or p.get("post_date", "9999-99-99") >= cutoff3)
                    and p.get("viral_score", 0) >= min_vs3
                    and (sel_cat3 == "전체" or p.get("category") == sel_cat3)
                ]

                # 정렬
                if sort3 == "바이럴 점수 순":
                    t3.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
                else:
                    t3.sort(key=lambda x: x.get("post_date", ""), reverse=True)

                # 집계 메트릭 (4열)
                top_vs3   = t3[0].get("viral_score", 0) if t3 else 0
                avg_vs3   = sum(p.get("viral_score", 0) for p in t3) / max(len(t3), 1)
                ttl_views = sum(p.get("instagram_views", 0) for p in t3)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("바이럴 포스트",   f"{len(t3):,}개")
                c2.metric("최고 바이럴 점수", f"{top_vs3:,.0f}")
                c3.metric("평균 바이럴 점수", f"{avg_vs3:,.0f}")
                c4.metric("총 조회수",        fmt_num(ttl_views))

                if not t3:
                    st.warning("조건에 맞는 바이럴 컨텐츠가 없습니다. 필터를 조정해보세요.")
                else:
                    # TOP 20 바이럴 점수 차트
                    df_v3 = pd.DataFrame([
                        {
                            "해시태그":    "#" + p.get("hashtag", ""),
                            "바이럴 점수": p.get("viral_score", 0),
                            "카테고리":    p.get("category", ""),
                        }
                        for p in t3[:50]
                    ])
                    fig3 = px.bar(
                        df_v3.sort_values("바이럴 점수").tail(20),
                        x="바이럴 점수", y="해시태그", orientation="h",
                        color="카테고리", title="TOP 20 바이럴 점수",
                        height=380,
                    )
                    fig3.update_layout(showlegend=True, legend_title_text="카테고리")
                    st.plotly_chart(fig3, use_container_width=True)

                    # 페이지네이션 + 4열 그리드 (render_viral_card 사용)
                    total_p3 = max(1, (len(t3) - 1) // ads_pp3 + 1)
                    page3 = st.selectbox(
                        f"페이지 선택 (총 {total_p3}페이지)",
                        range(1, total_p3 + 1),
                        format_func=lambda x: f"페이지 {x}/{total_p3}",
                        key="t3_page"
                    )
                    si3 = (page3 - 1) * ads_pp3
                    ei3 = si3 + ads_pp3
                    show3 = t3[si3:ei3]
                    st.caption(f"{si3+1} – {min(ei3, len(t3))} / {len(t3)}개")

                    for i in range(0, len(show3), 4):
                        cols3 = st.columns(4)
                        for j, post in enumerate(show3[i:i+4]):
                            render_viral_card(post, cols3[j])


# ─────────────────────────────────────────────────
if __name__ == "__main__":
    main()
