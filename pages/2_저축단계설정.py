import streamlit as st
import plotly.graph_objects as go

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

# ── 세션 초기화 ──────────────────────────────────────────────────────────────
if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5
if "expenses" not in st.session_state:
    st.session_state.expenses = []

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

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 본인의 정보가 맞는지 확인")
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=100000, max_value=10000000,
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
        
st.write("---")

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
