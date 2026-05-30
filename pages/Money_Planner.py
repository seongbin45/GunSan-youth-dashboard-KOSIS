import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px

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
    
    if target == "Household_Ledger":
        st.switch_page("pages/Household_Ledger.py")
    elif target == "finance":
        st.switch_page("pages/5_금융용어.py")
    elif target == "Savings_Step_Setting_Guide":
        st.switch_page("pages/Savings_Step_Setting_Guide.py")
    elif target == "Government_Backed_Benefits":
        st.switch_page("pages/3_정부 지원 혜택 목록.py")

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

# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("💰 머니 플래너")
st.markdown("#### 금융 미경험 청년을 위한 저축·소비 습관 서비스")
st.divider()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 기본 정보 입력")
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=10000, max_value=10000000,
        value=st.session_state.income, step=100000,
        format="%d"
    )
    st.session_state.income = income

    st.subheader("🎚️ 저축 강도 선택 (1~10단계)")
    level = st.slider(
        "1 = 여가 최우선 ~ 10 = 생존형 저축",
        min_value=1, max_value=10,
        value=st.session_state.level
    )
    st.session_state.level = level

    lv = LEVELS[level]
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
    save_amt    = int(income * lv['save'])
    fix_amt     = int(income * lv['fix'])
    leisure_amt = int(income * lv['leisure'])

    metrics = [
        ("💎 저축 목표",     save_amt,    lv['color']),
        ("🏠 고정비 예산",   fix_amt,     "#2196F3"),
        ("🎉 여가·식비 예산", leisure_amt, "#4CAF50"),
    ]
    for label, amt, color in metrics:
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:10px; padding:14px 20px; margin-bottom:10px;
                    border-left:5px solid {color};">
            <span style="color:#555; font-size:0.9em">{label}</span><br>
            <span style="font-size:1.6em; font-weight:bold; color:#222">
                {amt:,}원
            </span>
            <span style="color:#888; font-size:0.85em"> / 월</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("#### 🗺️ 왼쪽 사이드바에서 기능을 선택하세요")
cols = st.columns(4)
pages = [
    ("📒 가계부",        "수입·지출 기록 및 월별 분석"),
    ("🎯 저축단계 상세", "단계별 상세 가이드 및 팁"),
    ("🎁 청년 혜택",     "국가 청년 금융 지원 정보"),
    ("📚 금융 용어",     "꼭 알아야 할 금융 개념 정리"),
]
for col, (title, desc) in zip(cols, pages):
    with col:
        st.info(f"**{title}**\n\n{desc}")

st.write("---")

