import streamlit as st

st.set_page_config(page_title="FinFit", page_icon="💚", layout="wide")

st.title("💚 FinFit")
st.subheader("청년이 받아야 할 혜택을, AI가 먼저 찾아줍니다")

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/4_군산시민 맞춤 혜택 찾기.py", label="🎁 내 혜택 찾기", icon="🎁")
    st.caption("나이·소득·지역 입력하면 맞춤 혜택 바로 추천")
with col2:
    st.page_link("pages/2_금융용어.py", label="📚 금융 용어", icon="📚")
    st.caption("CMA, ETF, 청년도약계좌... 쉽게 설명해줌")
with col3:
    st.page_link("pages/3_AI상담.py", label="🤖 AI에게 물어보기", icon="🤖")
    st.caption("자연어로 질문하면 Agent가 알아서 답변")
