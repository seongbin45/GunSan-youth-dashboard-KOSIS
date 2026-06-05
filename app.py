import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px
import gspread # 사용자 피드백 도구
import json # 사용자 피드백 도구
from datetime import datetime # 사용자 피드백 도구


st.set_page_config(page_title="FinFit", page_icon="💰", layout="wide")

# ── 세션 초기화 ──────────────────────────────────────────────────────────────
if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5
if "expenses" not in st.session_state:
    st.session_state.expenses = []



# 주소창의 흔적을 감지해서 페이지를 이동시키는 네비게이터 역할을 합니다.
if "page" in st.query_params:
    target = st.query_params["page"]
    st.query_params.clear() # 무한 루프 방지를 위해 흔적 지우기
    
    if target == "benefit":
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")
    elif target == "finance":
        st.switch_page("pages/5_금융용어.py")
    elif target == "ai":
        st.switch_page("pages/2_AI와_대화하기.py")
    elif target == "Household_Ledger":
        st.switch_page("pages/Household_Ledger.py")
    elif target == "Savings_Step_Setting_Guide":
        st.switch_page("pages/Savings_Step_Setting_Guide.py")
    elif target == "Government_Backed_Benefits":
        st.switch_page("pages/3_정부 지원 혜택 목록.py")



st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    
    .header-container {
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 2rem;
    }
    
    .header-title {
        font-size: 3em;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.2em;
    }
    
    .header-subtitle {
        font-size: 1.3em;
        color: #666666;
        font-weight: 500;
        margin-bottom: 2em;
    }
    
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 6px solid;
        transition: all 0.3s ease;
        min-height: 350px;
        display: flex;
        flex-direction: column;
    }
    
    .feature-card:hover {
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-6px);
    }
    
    .card-icon {
        font-size: 3.5em;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-size: 1.6em;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.8rem;
    }
    
    .card-description {
        font-size: 1em;
        color: #555555;
        line-height: 1.7;
        margin-bottom: 1.5rem;
        flex-grow: 1;
    }
    
    .card-features {
        background: linear-gradient(135deg, #f5f5f5 0%, #f9f9f9 100%);
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .card-features-title {
        font-size: 0.9em;
        font-weight: 700;
        color: #333333;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    .feature-item {
        font-size: 0.95em;
        color: #444444;
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .feature-item:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    .feature-item:last-child {
        margin-bottom: 0;
    }
    
    div[data-testid="stButton"] > button {
        width: 100%;
        font-size: 1.05em !important;
        font-weight: 600 !important;
        padding: 0.8em 1.5em !important;
        height: auto !important;
        min-height: 45px !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .card-red {
        border-left-color: #FF6B6B;
    }
    
    .card-teal {
        border-left-color: #20B2AA;
    }
    
    .card-mint {
        border-left-color: #95E1D3;
    }

    .card-peach {
        border-left-color: #FF9E7D;
    }
    
    .card-blue {
        border-left-color: #579BB1;
    }

    .card-pastel-milk {
        border-left-color: #AEC6CF;
    }
    
    .card-pastel-powder {
        border-left-color: #B0C4DE;
    }
    
    .card-pastel-ice {
        border-left-color: #BCEEFA;
    }
    

    .card-pastel-fog {
        border-left-color: #C1D3DB;
    }

    
    .card-lavender {
        border-left-color: #A7BBC7;
    }
    
    .card-yellow {
        border-left-color: #F4D160;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stat-card:nth-child(2) {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
    }
    
    .stat-card:nth-child(3) {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
    }
    
    .stat-number {
        font-size: 2.2em;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.95em;
        opacity: 0.95;
    }
    
    hr {
        margin: 3rem 0;
        border: none;
        border-top: 2px solid #f0f0f0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #999999;
        font-size: 0.95em;
        border-top: 1px solid #f0f0f0;
    }
    
    @media (max-width: 768px) {
        .header-title {
            font-size: 2.2em;
        }
        
        .header-subtitle {
            font-size: 1.1em;
        }
        
        .feature-card {
            min-height: 320px;
        }
    }
</style>
""", unsafe_allow_html=True)


LEVELS = {
    1:  {"name":"여가 최우선",    "save":0.05, "fix":0.45, "leisure":0.50, "color":"#4CAF50"},
    2:  {"name":"여가 중심",      "save":0.10, "fix":0.50, "leisure":0.40, "color":"#8BC34A"},
    3:  {"name":"균형 여가형",    "save":0.15, "fix":0.55, "leisure":0.30, "color":"#CDDC39"},
    4:  {"name":"생활 균형형",    "save":0.20, "fix":0.55, "leisure":0.25, "color":"#FFEB3B"},
    5:  {"name":"균형형",         "save":0.25, "fix":0.55, "leisure":0.20, "color":"#FFC107"},
    6:  {"name":"저축 균형형",    "save":0.30, "fix":0.55, "leisure":0.15, "color":"#FF9800"},
    7:  {"name":"저축 집중형",    "save":0.40, "fix":0.50, "leisure":0.10, "color":"#FF5722"},
    8:  {"name":"고강도 저축형",    "save":0.50, "fix":0.45, "leisure":0.05, "color":"#F44336"},
    9:  {"name":"열정 저축형",      "save":0.65, "fix":0.35, "leisure":0.00, "color":"#E91E63"},
    10: {"name":"목표 달성형",    "save":0.80, "fix":0.20, "leisure":0.00, "color":"#9C27B0"},
}
st.session_state.LEVELS = LEVELS

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

    # ✅ 이 세 줄 주석 해제 (삭제 말고 살려야 해)
    save_amt    = int(income * lv['save'])
    fix_amt     = int(income * lv['fix'])
    leisure_amt = int(income * lv['leisure'])

    # ✅ metrics 리스트 정의 추가
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
        <div style="background:#f8f9fa; border-radius:10px; padding:14px 20px; margin-bottom:10px;
                    border-left:5px solid {color};">
            <span style="color:#555; font-size:0.9em">
                {label.split()[0]}&nbsp;
                <span class="tooltip-wrap" tabindex="0">
                    {term}
                    <span class="tooltip-box">{tip}</span>
                </span>
            </span><br>
            <span style="font-size:1.6em; font-weight:bold; color:#222">
                {amt:,}원
            </span>
            <span style="color:#888; font-size:0.85em"> / 월</span>
        </div>
        """, unsafe_allow_html=True)



st.write("---")

st.set_page_config(page_title="저축단계 상세", page_icon="🎯", layout="wide")
st.title("🎯 상세 가이드")
st.markdown("#### 사회초년생을 위한 저축·소비 습관 계획 서비스")
st.divider()

if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5

LEVELS = {
    1:  {"name":"여가 최우선",  "save":0.05,"fix":0.45,"leisure":0.50,"color":"#4CAF50",
         "tips":["친구 모임, 취미 생활 충분히 즐기기","남는 돈은 CMA통장에 자동이체","소비 패턴 파악하는 시기"]},
    2:  {"name":"여가 중심",    "save":0.10,"fix":0.50,"leisure":0.40,"color":"#8BC34A",
         "tips":["여가비 예산 세우고 그 안에서 즐기기","적금 1개 만들어 자동이체 설정","지출 앱으로 소비 기록 시작"]},
    3:  {"name":"균형 여가형",  "save":0.15,"fix":0.55,"leisure":0.30,"color":"#CDDC39",
         "tips":["청년희망적금 / 청년도약계좌 가입 검토","외식 횟수 주 2회로 줄이기","구독 서비스 점검 및 정리"]},
    4:  {"name":"생활 균형형",  "save":0.20,"fix":0.55,"leisure":0.25,"color":"#FFEB3B",
         "tips":["비상금 3개월치 먼저 만들기","교통비 할인카드 발급","식비는 식료품 위주로 전환"]},
    5:  {"name":"균형형",       "save":0.25,"fix":0.55,"leisure":0.20,"color":"#FFC107",
         "tips":["청년도약계좌 (월 최대 70만원) 적극 활용","점심은 도시락 또는 구내식당","여가는 무료·저가 문화활동 위주"]},
    6:  {"name":"저축 균형형",  "save":0.30,"fix":0.55,"leisure":0.15,"color":"#FF9800",
         "tips":["주거비 절감 방안 검토 (청년월세지원 신청)","카드 대신 체크카드 사용","월말 잔액 추가 저축 습관 만들기"]},
    7:  {"name":"저축 집중형",  "save":0.40,"fix":0.50,"leisure":0.10,"color":"#FF5722",
         "tips":["고정비 항목 전면 재검토","통신비 알뜰폰으로 전환 (월 1~2만원대)","여가는 한 달에 1~2회만"]},
    8:  {"name":"고강도 저축",  "save":0.50,"fix":0.45,"leisure":0.05,"color":"#F44336",
         "tips":["월세 부담 낮추기 (룸메이트 또는 고시원 검토)","식비는 직접 요리 위주","절약 챌린지 SNS 커뮤니티 참여"]},
    9:  {"name":"극한 저축",    "save":0.65,"fix":0.35,"leisure":0.00,"color":"#E91E63",
         "tips":["단기 목돈 마련 목표 설정 (1년 내)","불필요한 모든 지출 제거","정부 지원 식품바우처 등 최대한 활용"]},
    10: {"name":"생존형 저축",  "save":0.80,"fix":0.20,"leisure":0.00,"color":"#9C27B0",
         "tips":["생활비 최저 생계비 수준으로 제한","무료 와이파이·공공시설 적극 이용","번아웃 주의: 1~2개월 단기 목표로 운영"]},
}

income = st.session_state.income
level  = st.session_state.level


st.subheader(f"✅ 현재 선택: {level}단계 — {LEVELS[level]['name']}")

lv = LEVELS[level]
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
        <div style="font-size:1em; color:#555">{label}</div>
        <div style="font-size:2em; font-weight:bold; color:#222">{int(ratio*100)}%</div>
        <div style="font-size:1.2em; color:#444">{amt:,}원</div>
    </div>""", unsafe_allow_html=True)

st.markdown("#### 💡 이 단계 실천 팁")
for tip in lv["tips"]:
    st.markdown(f"- ✔️ {tip}")

st.divider()
st.subheader("📈 저축 목표 시뮬레이션")
months = st.slider("몇 개월 후 목표 확인?", 1, 36, 12)
monthly_save = int(income * lv["save"])
total_save   = monthly_save * months
st.success(f"**{months}개월 후 예상 저축액: {total_save:,}원** (월 {monthly_save:,}원 × {months}개월)")

st.write("---")

st.set_page_config(page_title="청년 머니 플래너", page_icon="💰", layout="wide")


LEVELS = {
    1:  {"name":"여가 최우선",    "save":0.05, "fix":0.45, "leisure":0.50, "color":"#4CAF50"},
    2:  {"name":"여가 중심",      "save":0.10, "fix":0.50, "leisure":0.40, "color":"#8BC34A"},
    3:  {"name":"균형 여가형",    "save":0.15, "fix":0.55, "leisure":0.30, "color":"#CDDC39"},
    4:  {"name":"생활 균형형",    "save":0.20, "fix":0.55, "leisure":0.25, "color":"#FFEB3B"},
    5:  {"name":"균형형",         "save":0.25, "fix":0.55, "leisure":0.20, "color":"#FFC107"},
    6:  {"name":"저축 균형형",    "save":0.30, "fix":0.55, "leisure":0.15, "color":"#FF9800"},
    7:  {"name":"저축 집중형",    "save":0.40, "fix":0.50, "leisure":0.10, "color":"#FF5722"},
    8:  {"name":"고강도 저축",    "save":0.50, "fix":0.45, "leisure":0.05, "color":"#F44336"},
    9:  {"name":"극한 저축",      "save":0.65, "fix":0.35, "leisure":0.00, "color":"#E91E63"},
    10: {"name":"생존형 저축",    "save":0.80, "fix":0.20, "leisure":0.00, "color":"#9C27B0"},
}
st.session_state.LEVELS = LEVELS
    

# 전체 단계 비교표
st.subheader("📊 전체 단계 비교")
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

st.write("---")





st.divider()
st.markdown("#### 🗺️ 아래에서 기능을 선택해주세요")
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


# 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    # 카드 전체를 <a> 태그로 감싸고 주소 뒤에 ?page=Household_Ledger이 붙도록 만듭니다.
    cols = st.columns(4)
    st.markdown("""
    <a href="/?page=Household_Ledger" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-yellow">
            <div class="card-icon">📒</div>
            <div class="card-title">가계부</div>
            <div class="card-description">
                내역을 입력만 하면<br/>
                수입·지출 기록 및 월별 자동 분석
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 것들을 얻을 수 있어요</span>
                <div class="feature-item">고정비, 식비, 여가 등 정보</div>
                <div class="feature-item">구글 시트에 데이터 자동 동기화</div>
                <div class="feature-item">구글 시트 데이터 초기화 가능</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 클릭되면 안전하게 st.switch_page가 작동합니다.
    if st.button("지금 입력해보기 →", key="btn_benefit", use_container_width=True):
        st.switch_page("pages/Household_Ledger.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-mint">
            <div class="card-icon">📚</div>
            <div class="card-title">금융 용어</div>
            <div class="card-description">
                CMA, ETF, 청년도약계좌,<br/>
                전세대출 등<br/>
                경제 신문에 나오는<br/> 
                어려운 용어를<br/>
                쉽게 설명해줍니다
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
        <div class="feature-card card-pastel-fog">
            <div class="card-icon">🚀</div>
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
    
    if st.button("AI와 상담하기 →", key="btn_ai_agent", use_container_width=True):
        st.switch_page("pages/2_AI와_대화하기.py")


#st.divider()

# 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    cols = st.columns(4)
    st.markdown("""
    <a href="/?page=benefit" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-peach">
            <div class="card-icon">🎁</div>
            <div class="card-title">군산 맞춤 혜택 찾기</div>
            <div class="card-description">
                나이, 소득, 지역만 입력하면<br/>
                군산시에서 나에게 주는<br/>
                나에게 맞는 혜택을 자동 추천
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
    if st.button("지금 혜택 찾아보기 →", key="btn_Savings_Step_Setting_Guid_For", use_container_width=True):
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=Government_Backed_Benefits" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-pastel-powder">
            <div class="card-icon">🌐</div>
            <div class="card-title">정부 지원 혜택</div>
            <div class="card-description">
                국가 청년 금융 지원 정보<br/>
                정부 사이트 실시간 동기화<br/>
                모든 정책을 한 화면에 보여줍니다
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 정보를 얻을 수 있어요</span>
                <div class="feature-item">청년도약계좌, 햇살론 등</div>
                <div class="feature-item">신청 방법 및 기한</div>
                <div class="feature-item">공식 사이트 링크</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("확인해 보러 가기 →", key="btn_finances", use_container_width=True):
        st.switch_page("pages/3_정부 지원 혜택 목록.py")

with col3:
    # onclick 내부의 window.parent를 제거하여 보안 차단을 우회합니다.
    st.markdown("""
    <div class="feature-card card-blue" style="cursor: pointer;" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('바로 확인해보기')).click();">
        <div class="card-icon">🎯</div>
        <div class="card-title">저축단계 상세 가이드</div>
        <div class="card-description">
            몇 개월 후 도달 금액을<br/>
            미리 확인할 수 있어요
        </div>
        <div class="card-features">
            <span class="card-features-title">이런 자료들을 얻을 수 있어요</span>
            <div class="feature-item">단계별 상세 가이드 및 팁</div>
            <div class="feature-item">목표 금액 시뮬레이션</div>
            <div class="feature-item">전체 단계 비교 그래프</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 자바스크립트에 의해 클릭되며 데이터 초기화 없이 페이지를 이동시킵니다.
    if st.button("바로 확인해보기 →", key="btn_ai", use_container_width=True):
        st.switch_page("pages/Savings_Step_Setting_Guide.py")



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### github.com 주소 뒤에 ?raw=true 추가
github_image_url = "https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS/blob/9a0bf10dfd74407e81691b274a1b8e9f690e7104/tests/Image/%EC%A0%9C%EB%AA%A9%EC%9D%84%20%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94.%20(7).png?raw=true"

### 스트림릿에 이미지 출력
st.image(github_image_url, use_container_width=True)



# 1. ⚠️ 핵심 개선점: 캐싱 추가 (55분마다 한 번만 구글 인증 수행)
@st.cache_resource(ttl=3300)
def get_gspread_client():
    # Secrets에서 통째로 저장된 JSON 문자열을 가져옴
    json_string = st.secrets["gspread_json"]
    
    # 문자열을 파이썬 딕셔너리로 변환
    credentials = json.loads(json_string)
    
    # 구글 서비스 계정 인증 수행
    gc = gspread.service_account_from_dict(credentials)
    return gc
    
# UI 안내 문구 출력
st.markdown("### 💌 서비스 의견 공유")
st.markdown("""
**저희는 더 나은 경험을 드리기 위해   
꾸준히 준비 중입니다.**  

소중한 의견을 들려주시면,  
서비스 개선에 큰 도움이 됩니다!  

🔒 개인정보 보호 |
"""
   '<a href="https://docs.google.com/forms/d/e/1FAIpQLSco-O4cGhbt1iMOwrEkqX5Vt0-8ctAtCxM5Z6JjmFlP-Uqq-Q/viewform?usp=header" target="_blank"><button style="color: blue;">설문 링크로 이동</button></a>', 
    unsafe_allow_html=True        
           )


# 의견 입력 창
user_feedback = st.text_area(
    "자유롭게 적어주세요 👇", 
    placeholder="예: 이런 기능이 추가되면 좋겠어요 / 이 부분이 사용하기 조금 불편해요"
)

# 의견 남기기 버튼 (CTA)
if st.button("피드백 남기기", use_container_width=True):
    if user_feedback.strip() == "":
        st.warning("내용을 입력한 후 버튼을 눌러주세요! ⚠️")
    else:
        try:
            # 2. 구글 인증 및 시트 열기 (이제 캐시된 클라이언트를 빠르게 불러옴)
            gc = get_gspread_client()
            sh = gc.open_by_key(st.secrets["spreadsheet_id"])
            
            # 시트 이름으로 명확하게 지정하는 것을 권장하나, 인덱스(0)도 무방합니다.
            worksheet = sh.get_worksheet(0) 
            
            # 3. 데이터 추가
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, user_feedback])
            
            # 4. 제출 성공 완료 메시지 및 시각 효과
            st.balloons()
            st.success("""
            🎉 **소중한 피드백이 성공적으로 전달되었어요!**  
            보내주신 다정한 말씀과 조언은  
            서비스 개선에 적극 반영하겠습니다.  
            앞으로도 많은 기대 부탁드려요! 🙏
            """)
            
        except Exception as e:
            st.error(f"데이터 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")





