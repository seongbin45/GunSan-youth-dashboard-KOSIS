import streamlit as st
import textwrap
import pandas as pd

from finfit_youth.config import inject_finfit_theme

st.set_page_config(page_title="청년 혜택 정보", page_icon="🎁", layout="wide")
inject_finfit_theme()

st.markdown("""
<style>
.stApp { background: #111111 !important; }

/* Aggressive reset for tab top space */
.stTabs, 
.stTabs > div,
.stTabs [data-baseweb="tab-panel"],
.stTabs [data-baseweb="tab-panel"] > div,
.stTabs [data-baseweb="tab-panel"] > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    margin-bottom: 2px !important;
}
.stTextInput {
    margin-top: 0 !important;
    margin-bottom: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# Consistent header with other pages (dark, TSX-like)
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px; margin:-12px -12px 4px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div onclick="window.history.back()" style="width:36px;height:36px;background:#222;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;">
      <span style="font-size:18px;color:#aaa;">←</span>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">📮 국가 청년 금융 지원 상품</div>
      <div style="font-size:12px;color:#888;">공식 데이터 기반 • 자세한 내용은 각 사이트에서 확인</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Extra CSS to kill any remaining top space after header
st.markdown("""
<style>
.stRadio, .stTextInput { margin-top: 0 !important; margin-bottom: 4px !important; }
</style>
""", unsafe_allow_html=True)

# Pull content up right after header
st.markdown('<div style="margin-top: -8px;">', unsafe_allow_html=True)

# Data outside tabs for consistency and to prevent errors
data = [
    {"분류":"적금·저축",  "상품명":"청년도약계좌",
     "대상":"만 19~34세, 연소득 7,500만원 이하",
     "혜택":"월 최대 70만원 납입 → 정부 기여금 + 비과세 혜택, 5년 만기",
     "신청":"은행 앱 (국민·신한·하나·우리·농협 등)", "🔗":"https://www.kinfa.or.kr"},
    {"분류":"적금·저축",  "상품명":"청년희망적금 (종료)",
     "대상":"만 19~34세, 연소득 3,600만원 이하",
     "혜택":"2년 만기, 저축장려금 + 비과세 (신규 모집 종료, 참고용)",
     "신청":"—", "🔗":""},
    {"분류":"주거",       "상품명":"청년월세 한시 특별지원",
     "대상":"만 19~34세 독립거주 청년, 소득 기준 충족",
     "혜택":"월 최대 20만원 × 12개월 (240만원) 현금 지원",
     "신청":"복지로 (bokjiro.go.kr)", "🔗":"https://www.bokjiro.go.kr"},
    {"분류":"주거",       "상품명":"청년 전세임대주택",
     "대상":"대학생·취준생·만 19~39세 사회초년생",
     "혜택":"기존 주택 전세계약 후 저렴하게 재임대, 최장 6년 거주",
     "신청":"LH 청약센터", "🔗":"https://apply.lh.or.kr"},
    {"분류":"취업·소득",  "상품명":"국민취업지원제도",
     "대상":"만 15~69세 취업취약계층 (청년 우선)",
     "혜택":"구직촉진수당 월 50만원 × 6개월 + 취업지원 서비스",
     "신청":"워크넷 (work.go.kr)", "🔗":"https://www.work.go.kr"},
    {"분류":"취업·소득",  "상품명":"청년내일채움공제 (청년형)",
     "대상":"중소·중견기업 취업 청년 (만 15~34세)",
     "혜택":"2년간 청년 400만원 + 기업·정부 지원 → 총 1,200만원",
     "신청":"청년내일채움공제 포털", "🔗":"https://www.work.go.kr/youngtomorrow"},
    {"분류":"신용·금융",  "상품명":"햇살론유스",
     "대상":"만 19~34세, 연소득 3,500만원 이하 또는 신용점수 하위 20%",
     "혜택":"최대 1,200만원 저금리 대출 (연 3.5~4.5%)",
     "신청":"서민금융진흥원, 농협·신협 등", "🔗":"https://www.kinfa.or.kr"},
    {"분류":"신용·금융",  "상품명":"청년 신용회복 지원",
     "대상":"소액 연체 청년",
     "혜택":"채무조정, 신용상담, 금융교육 지원",
     "신청":"신용회복위원회", "🔗":"https://www.ccrs.or.kr"},
    {"분류":"교육·자기계발","상품명":"국민내일배움카드",
     "대상":"만 15세 이상 취업·재직·자영업자",
     "혜택":"5년간 300~500만원 직업훈련비 지원",
     "신청":"HRD-Net (hrd.go.kr)", "🔗":"https://www.hrd.go.kr"},
]

df = pd.DataFrame(data)

# Category filter - using radio for tight spacing (no tab panel empty space)
categories = ["전체", "적금·저축", "주거", "취업·소득", "신용·금융", "교육·자기계발"]
active_cat = st.radio("분류", categories, horizontal=True, label_visibility="collapsed")

# Shared filter controls 
keyword = st.text_input("🔍 검색 (상품명·혜택 키워드)", key="gov_search")

def render_benefit_list(filtered_df):
    if filtered_df.empty:
        st.info("조건에 맞는 혜택이 없습니다.")
        return
    # Tight wrapper to remove top space
    st.markdown('<div style="margin-top: -8px;">', unsafe_allow_html=True)
    for _, row in filtered_df.iterrows():
        with st.expander(f"**{row['상품명']}** — {row['분류']}"):
            st.markdown(f"**대상:** {row['대상']}")
            st.markdown(f"**혜택:** {row['혜택']}")
            st.markdown(f"**신청:** {row['신청']}")
            if row["🔗"]:
                st.markdown(f"[🌐 공식 사이트 바로가기]({row['🔗']})")
    st.markdown('</div>', unsafe_allow_html=True)

# Filter and render based on active_cat (no tabs, tight layout)
filtered = df.copy()
if active_cat != "전체":
    filtered = filtered[filtered["분류"] == active_cat]
if keyword:
    mask = (filtered["상품명"].str.contains(keyword, case=False, na=False) |
            filtered["혜택"].str.contains(keyword, case=False, na=False))
    filtered = filtered[mask]

render_benefit_list(filtered)

st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption(
    "📌 이 페이지는 **대표 국가 청년 금융 상품 안내(수동 정리본)** 입니다. "
    "지원 내용은 정책 변경에 따라 달라질 수 있으니 반드시 공식 사이트에서 최신 정보를 확인하세요."
)
st.caption(
    "📡 온통청년 **실시간/캐시 정책 목록·동기화** 는 "
    "`7_청년혜택업데이트` 페이지와 맞춤 매칭(`4_군산시민 맞춤 혜택 찾기`)을 이용하세요."
)

