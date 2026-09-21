import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px
# (gspread/json/datetime imports removed - now handled inside centralized render_feedback_form)
import plotly.graph_objects as go # 저축 상세 가이드(비교표)


st.set_page_config(page_title="FinFit", page_icon="💰", layout="wide")

# ── 세션 초기화 ──────────────────────────────────────────────────────────────
if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "onboarding_completed" not in st.session_state:
    st.session_state.onboarding_completed = False

# ── 온보딩 게이트 (프로토타입 스타일) ────────────────────────────────────────
if not st.session_state.onboarding_completed:
    st.switch_page("pages/Onboarding.py")



# 주소창 ?page= 슬러그 라우팅 (미지 값 → FinFit 404 UI)
from finfit_youth.page_router import handle_query_page_param

if handle_query_page_param():
    st.stop()  # 의도적: 홈 본문과 404를 겹치지 않음



st.markdown("""
<style>
/* ============================================
   FinFit Unified Theme + Common CSS (dark mode for entire page)
   Background: #111111 dark
   ============================================ */

:root {
    --finfit-primary: #6366F1;
    --finfit-primary-dark: #5855EB;
    --finfit-gradient: linear-gradient(135deg, #6366F1 0%, #8B5CF6 60%, #A78BFA 100%);
    --finfit-bg: #111111;
    --finfit-card: #1a1a1a;
    --finfit-text: #f0f0f0;
    --finfit-muted: #888888;
    --finfit-border: #333333;
}

/* Base - entire page background (as requested for full page) */
.main, .stApp, body, .block-container, .stMain, .stApp > div {
    background-color: #111111 !important;
}

h1, h2, h3, h4, h5 {
    color: var(--finfit-text) !important;
}

/* Header (used on Home and main landing) */
.header-container {
    text-align: center;
    margin-bottom: 1.5rem;
    padding-top: 1rem;
}
.header-title {
    font-size: 2.4em;
    font-weight: 800;
    color: var(--finfit-text);
    letter-spacing: -0.02em;
}
.header-subtitle {
    font-size: 1.05em;
    color: var(--finfit-muted);
    font-weight: 500;
    margin-top: 0.25rem;
}

/* Standard feature / content cards */
.feature-card {
    background: var(--finfit-card);
    border-radius: 20px;                 /* stronger rounding like prototype */
    padding: 1.75rem 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--finfit-border);
    transition: all 0.2s ease;
}
.feature-card:hover {
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.10);
    transform: translateY(-2px);
}

/* Colored left border variants (keep for backward compat) */
.card-yellow  { border-left: 6px solid #F4D160; }
.card-mint    { border-left: 6px solid #95E1D3; }
.card-peach   { border-left: 6px solid #FF9E7D; }
.card-blue    { border-left: 6px solid #579BB1; }
.card-pastel-fog { border-left: 6px solid #C1D3DB; }

/* Asset / Summary Card (big gradient one from prototype) */
.asset-card {
    background: var(--finfit-gradient);
    color: white;
    border-radius: 20px;
    padding: 20px 22px;
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.35);
    position: relative;
    overflow: hidden;
}
.asset-card .sub-metric {
    background: rgba(255,255,255, 0.18);
    border-radius: 14px;
    padding: 10px 14px;
}

/* Progress bars */
.finfit-progress {
    height: 10px;
    background: #E5E7EB;
    border-radius: 999px;
    overflow: hidden;
}
.finfit-progress > div {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}
.progress-green { background: linear-gradient(90deg, #10B981, #34D399); }
.progress-yellow { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.progress-red   { background: linear-gradient(90deg, #EF4444, #F97316); }
.progress-indigo { background: var(--finfit-gradient); }

/* Stat pills / small cards */
.stat-pill {
    background: white;
    border-radius: 16px;
    padding: 12px 14px;
    border: 1px solid var(--finfit-border);
}
.stat-pill .label { font-size: 10px; color: #6B7280; }
.stat-pill .value { font-size: 18px; font-weight: 700; color: var(--finfit-text); }

/* Quick action / grid tiles (from prototype) */
.action-tile {
    background: #EEF0FF;
    border-radius: 16px;
    padding: 14px 10px;
    text-align: center;
    transition: all 0.2s;
}
.action-tile:hover { filter: brightness(0.97); }
.action-tile .icon { font-size: 22px; }
.action-tile .label { font-size: 11px; font-weight: 700; color: #6366F1; }
.action-tile .sub { font-size: 10px; color: #9CA3AF; }

/* Benefits / NEW banner */
.benefit-banner {
    background: var(--finfit-gradient);
    color: white;
    border-radius: 20px;
    padding: 16px 18px;
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.35);
}

/* Transaction / list rows */
.tx-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: white;
    border-bottom: 1px solid #F3F4F6;
}
.tx-row:last-child { border-bottom: none; }
.tx-icon {
    width: 36px; height: 36px; border-radius: 999px;
    background: #F5F7FF; display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}

/* Buttons - global nicer look */
div[data-testid="stButton"] > button {
    width: 100%;
    font-size: 0.95em !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
    height: auto !important;
    min-height: 42px !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: var(--finfit-primary) !important;
    color: white !important;
}

/* Badges */
.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
}
.badge-new { background: #6366F1; color: white; }
.badge-dday { background: #FEF3C7; color: #92400E; }

/* Search / input polish */
.stTextInput > div > div > input {
    border-radius: 14px !important;
    border: 1px solid var(--finfit-border) !important;
}

/* Footer / small text */
.footer {
    text-align: center;
    padding: 1.5rem 0;
    color: #9CA3AF;
    font-size: 0.85em;
}

/* Responsive */
@media (max-width: 768px) {
    .header-title { font-size: 1.9em; }
    .feature-card { padding: 1.25rem 1rem; min-height: auto; }
}
</style>
""", unsafe_allow_html=True)


from finfit_youth.config import LEVELS, calculate_budget, render_feedback_form, inject_finfit_theme
st.session_state.LEVELS = LEVELS  # centralized (removed local duplicate)

# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("💰 FinFit")
st.markdown("#### 금융 미경험 청년을 위한 저축·소비 습관 서비스")
st.divider()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 기본 정보 입력")
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=10000, max_value=10000000,
        value=st.session_state.income, step=100000,
        format="%d",
        help="매달 정기적으로 받는 돈이에요. 알바비, 용돈, 급여 모두 포함해서 입력하세요. 정확하지 않아도 괜찮아요!"
    )
    st.session_state.income = income

    st.subheader("🎚️ 어떤 스타일로 돈을 모을까요? (1~10단계)")
    level = st.slider(
        "여유롭게 즐기기  ←    →  최대한 모으기",
        min_value=1, max_value=10,
        value=st.session_state.level,
        help="숫자가 낮을수록 여가·식비에 더 쓰고, 높을수록 저축을 더 많이 해요. 지금 당장 완벽하게 안 맞아도 괜찮아요, 나중에 언제든 바꿀 수 있어요!"
    )
    st.session_state.level = level

    lv = LEVELS[level]
    save_pct    = int(lv['save']*100)
    fix_pct     = int(lv['fix']*100)
    leisure_pct = int(lv['leisure']*100)
    monthly     = st.session_state.income
    
    st.markdown(f"""
    <div style="background:{lv['color']}22; border-left:5px solid {lv['color']};
                padding:14px 18px; border-radius:8px; margin-top:10px;">
        <b style="font-size:1.1em">{level}단계 · {lv['name']}</b><br>
        저축 <b>{int(lv['save']*100)}%</b> &nbsp;|&nbsp;
        고정비 <b>{int(lv['fix']*100)}%</b> &nbsp;|&nbsp;
        여가·식비 <b>{int(lv['leisure']*100)}%</b>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📊 이번 달 예산 배분")
    budget = calculate_budget(income, level)
    save_amt = budget["save"]
    fix_amt = budget["fix"]
    leisure_amt = budget["leisure"]
    lv = budget["level_info"]

    metrics = [
        ("💎 저축 목표",      save_amt,    lv['color']),
        ("🏠 고정비 예산",    fix_amt,     "#2196F3"),
        ("🎉 여가·식비 예산", leisure_amt, "#4CAF50"),
    ]

    # 👇 이 CSS 툴팁 블록 추가
    st.markdown("""
    <style>
    .tooltip-wrap {
        display: inline-block;
        position: relative;
        cursor: pointer;
        border-bottom: 1.5px dashed #aaa;
        color: inherit;
    }
    .tooltip-wrap .tooltip-box {
        visibility: hidden;
        opacity: 0;
        background: #1a1a1a;
        color: #fff;
        font-size: 0.82em;
        line-height: 1.6;
        border-radius: 8px;
        padding: 10px 14px;
        position: absolute;
        z-index: 999;
        bottom: 130%;
        left: 0%;
        transform: none;
        width: 220px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        transition: opacity 0.2s;
        pointer-events: none;
    }
    .tooltip-wrap:hover .tooltip-box,
    .tooltip-wrap:focus .tooltip-box {
        visibility: visible;
        opacity: 1;
    }
    .tooltip-wrap .tooltip-box::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 20px;       /* 기존 left: 50% → 20px로 변경 */
        transform: none;  /* 기존 translateX(-50%) 제거 */
        border: 6px solid transparent;
        border-top-color: #1a1a1a;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 👇 기존 metrics 루프를 이걸로 교체
    TERM_TIPS = {
        "💎 저축 목표":      ("저축", "쓰지 않고 모아두는 돈이에요.<br>이 금액을 매달 통장에 먼저 빼두는 게 핵심이에요!"),
        "🏠 고정비 예산":    ("고정비", "매달 비슷하게 나가는 돈이에요.<br>월세, 통신비, 교통비처럼 줄이기 어려운 지출들이에요."),
        "🎉 여가·식비 예산": ("여가·식비", "밥값, 카페, 취미, 쇼핑처럼<br>생활을 즐기는 데 쓰는 돈이에요."),
    }

    # ✅ for 루프가 with col2: 안에 들여쓰기 되어 있어야 해
    for label, amt, color in metrics:
        term, tip = TERM_TIPS[label]
        st.markdown(f"""
        <div style="background:#1a1a1a; border-radius:10px; padding:14px 20px; margin-bottom:10px;
                    border-left:5px solid {color};">
            <span style="color:#aaa; font-size:0.9em">
                {label.split()[0]}&nbsp;
                <span class="tooltip-wrap" tabindex="0">
                    {term}
                    <span class="tooltip-box">{tip}</span>
                </span>
            </span><br>
            <span style="font-size:1.6em; font-weight:bold; color:#eee">
                {amt:,}원
            </span>
            <span style="color:#888; font-size:0.85em"> / 월</span>
        </div>
        """, unsafe_allow_html=True)



st.write("---")

st.subheader("🎯 상세 가이드")

with st.expander("상세 가이드 보기"):
    from finfit_youth.config import LEVELS, calculate_budget
    if "income" not in st.session_state:
        st.session_state.income = 2000000
    if "level" not in st.session_state:
        st.session_state.level = 5
    
    income = st.session_state.income
    level  = st.session_state.level
    
    st.subheader(f"✅ 현재 선택: {level}단계 — {LEVELS[level]['name']}")
    
    budget = calculate_budget(income, level)
    lv = budget["level_info"]
    c1, c2, c3 = st.columns(3)
    for col, (label, ratio, color) in zip(
        [c1, c2, c3],
        [("💎 저축", lv["save"], lv["color"]),
         ("🏠 고정비", lv["fix"], "#2196F3"),
         ("🎉 여가·식비", lv["leisure"], "#4CAF50")]
    ):
        amt = int(income * ratio)
        col.markdown(f"""
        <div style="text-align:center; background:{color}22;
                    border-radius:12px; padding:20px; border-top:4px solid {color}">
            <div style="font-size:1em; color:#aaa">{label}</div>
            <div style="font-size:2em; font-weight:bold; color:#eee">{int(ratio*100)}%</div>
            <div style="font-size:1.2em; color:#ccc">{amt:,}원</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("#### 💡 이 단계 실천 팁")
    for tip in lv["tips"]:
        st.markdown(f"- ✔️ {tip}")
    
    st.divider()
    st.subheader("📈 저축 목표 시뮬레이션")
    months = st.slider("몇 개월 후 목표 확인?", 1, 36, 12)
    monthly_save = budget["save"]
    total_save = monthly_save * months
    st.success(f"**{months}개월 후 예상 저축액: {total_save:,}원** (월 {monthly_save:,}원 × {months}개월)")

st.write("---")

# (removed stray set_page_config and duplicate LEVELS import - using top-level centralized one)
    

# 전체 단계 비교표
st.subheader("📊 전체 단계 비교")

with st.expander("전체 단계 비교표 보기"):

    levels_list = list(LEVELS.items())
    fig = go.Figure()
    fig.add_bar(name="저축", x=[f"{k}단계" for k,_ in levels_list],
                y=[v["save"]*100 for _,v in levels_list], marker_color="#9C27B0")
    fig.add_bar(name="고정비", x=[f"{k}단계" for k,_ in levels_list],
                y=[v["fix"]*100 for _,v in levels_list], marker_color="#2196F3")
    fig.add_bar(name="여가·식비", x=[f"{k}단계" for k,_ in levels_list],
                y=[v["leisure"]*100 for _,v in levels_list], marker_color="#4CAF50")
    fig.update_layout(barmode="stack", height=350,
                      yaxis_title="비율 (%)", margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
    




st.divider()
st.markdown("#### 🗺️ 아래에서 기능을 선택해주세요\n(설정에서 온보딩 다시 보기 가능)")
cols = st.columns(4)
#pages = [
    #("📒 가계부",        "수입·지출 기록 및 월별 분석"),
    #("🎯 저축단계 상세", "단계별 상세 가이드 및 팁"),
    #("🎁 청년 혜택",     "국가 청년 금융 지원 정보"),
    #("📚 금융 용어",     "꼭 알아야 할 금융 개념 정리"),
#]
#for col, (title, desc) in zip(cols, pages):
    #with col:
        #st.info(f"**{title}**\n\n{desc}")

#st.write("---")


# 세 가지 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    # 카드 전체를 <a> 태그로 감싸고 주소 뒤에 ?page=benefit이 붙도록 만듭니다.
    st.markdown("""
    <a href="/?page=benefit" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-red">
            <div class="card-icon">🎁</div>
            <div class="card-title">내 혜택 찾기</div>
            <div class="card-description">
                나이, 소득, 지역만 입력하면<br/>
                정부·군산시에서 나에게 주는<br/>
                금융 지원과 대출을 자동 추천
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 정보를 얻을 수 있어요</span>
                <div class="feature-item">50개 이상 청년 정책 매칭</div>
                <div class="feature-item">연 최대 1,000만원 이상 지원액</div>
                <div class="feature-item">신청 방법과 기한 안내</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 클릭되면 안전하게 st.switch_page가 작동합니다.
    if st.button("지금 혜택 찾아보기 →", key="btn_benefit", use_container_width=True):
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-teal">
            <div class="card-icon">📚</div>
            <div class="card-title">금융 용어</div>
            <div class="card-description">
                CMA, ETF, 청년도약계좌,<br/>
                전세대출... 경제 신문에 나오는<br/>
                어려운 용어를 쉽게 설명해줍니다
            </div>
            <div class="card-features">
                <span class="card-features-title">이 정도는 꼭 알아야 해요</span>
                <div class="feature-item">30개 금융 개념 정리</div>
                <div class="feature-item">실생활 예시로 이해</div>
                <div class="feature-item">개념 + 행동 가이드</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("금융 용어 배우기 →", key="btn_finance", use_container_width=True):
        st.switch_page("pages/5_금융용어.py")

with col3:
    st.markdown("""
    <a href="/?page=ai" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-mint">
            <div class="card-icon">💭</div>
            <div class="card-title">AI 금융 상담</div>
            <div class="card-description">
                "전세금 대출은 언제까지 나올까?"<br/>
                "내가 받을 수 있는 혜택이 뭐야?"<br/>
                "자연어로 물어보면 AI가 즉답
            </div>
            <div class="card-features">
                <span class="card-features-title">AI가 도와줄 수 있어요</span>
                <div class="feature-item">50개 청년 정책 데이터 학습</div>
                <div class="feature-item">실시간 금융 계산</div>
                <div class="feature-item">군산시 맞춤 정보</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("AI와 상담하기 →", key="btn_ai", use_container_width=True):
        st.switch_page("pages/2_AI와_대화하기.py")

st.divider()



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### github.com 주소 뒤에 ?raw=true 추가
github_image_url = "https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS/blob/9a0bf10dfd74407e81691b274a1b8e9f690e7104/tests/Image/%EC%A0%9C%EB%AA%A9%EC%9D%84%20%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94.%20(7).png?raw=true"

### 스트림릿에 이미지 출력
st.image(github_image_url, use_container_width=True)



render_feedback_form(key_prefix="app_main")





