import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="가계부", page_icon="📒", layout="wide")
st.title("📒 가계부")

if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5
if "LEVELS" not in st.session_state:
    st.session_state.LEVELS = {}

CATEGORIES = {
    "고정비":  ["월세/관리비","통신비","보험료","교통비","구독서비스"],
    "식비":    ["식료품","외식","카페·음료"],
    "여가":    ["취미·문화","여행","친구 모임","쇼핑"],
    "저축":    ["적금","비상금","투자"],
    "기타":    ["의료비","교육·자기계발","기타"],
}

# ── 지출 입력 ─────────────────────────────────────────────────────────────────
with st.expander("➕ 지출 추가", expanded=True):
    c1, c2, c3, c4, c5 = st.columns([2,2,2,2,1])
    with c1:
        exp_date  = st.date_input("날짜", value=date.today())
    with c2:
        cat_main  = st.selectbox("대분류", list(CATEGORIES.keys()))
    with c3:
        cat_sub   = st.selectbox("소분류", CATEGORIES[cat_main])
    with c4:
        amount    = st.number_input("금액 (원)", min_value=0, step=1000, format="%d")
    with c5:
        memo      = st.text_input("메모")
    if st.button("추가", use_container_width=True, type="primary"):
        if amount > 0:
            st.session_state.expenses.append({
                "날짜": str(exp_date), "대분류": cat_main,
                "소분류": cat_sub, "금액": amount, "메모": memo
            })
            st.success("추가됐어요!")
            st.rerun()

# ── 데이터 없을 때 ──────────────────────────────────────────────────────────
if not st.session_state.expenses:
    st.info("아직 지출 내역이 없어요. 위에서 추가해보세요!")
    st.stop()

df = pd.DataFrame(st.session_state.expenses)
df["금액"] = df["금액"].astype(int)

# ── 요약 ────────────────────────────────────────────────────────────────────
income  = st.session_state.income
total   = df[df["대분류"] != "저축"]["금액"].sum()
saved   = df[df["대분류"] == "저축"]["금액"].sum()
remain  = income - total - saved

st.divider()
cols = st.columns(4)
cols[0].metric("월 소득",     f"{income:,}원")
cols[1].metric("총 지출",     f"{total:,}원",  delta=f"-{total:,}원", delta_color="inverse")
cols[2].metric("저축",        f"{saved:,}원",  delta=f"+{saved:,}원")
cols[3].metric("남은 금액",   f"{remain:,}원", delta_color="normal")

st.divider()
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("카테고리별 지출")
    summary = df[df["대분류"] != "저축"].groupby("대분류")["금액"].sum().reset_index()
    fig = px.pie(summary, values="금액", names="대분류",
                 color_discrete_sequence=px.colors.qualitative.Pastel,
                 hole=0.4)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("목표 대비 달성 현황")
    LEVELS = st.session_state.get("LEVELS", {})
    lv = LEVELS.get(st.session_state.level, {"save":0.25,"fix":0.55,"leisure":0.20})
    targets = {
        "저축":    int(income * lv["save"]),
        "고정비":  int(income * lv["fix"]),
        "여가·식비": int(income * lv["leisure"]),
    }
    actuals = {
        "저축":    saved,
        "고정비":  df[df["대분류"] == "고정비"]["금액"].sum(),
        "여가·식비": df[df["대분류"].isin(["여가","식비"])]["금액"].sum(),
    }
    bar_df = pd.DataFrame({
        "항목": list(targets.keys()),
        "목표": list(targets.values()),
        "실제": [actuals[k] for k in targets],
    })
    fig2 = go.Figure()
    fig2.add_bar(name="목표", x=bar_df["항목"], y=bar_df["목표"],
                 marker_color="#CBD5E8")
    fig2.add_bar(name="실제", x=bar_df["항목"], y=bar_df["실제"],
                 marker_color="#F4A261")
    fig2.update_layout(barmode="group", height=320,
                       margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📋 지출 내역")
st.dataframe(df.sort_values("날짜", ascending=False).reset_index(drop=True),
             use_container_width=True, hide_index=True)

if st.button("🗑️ 전체 초기화", type="secondary"):
    st.session_state.expenses = []
    st.rerun()
