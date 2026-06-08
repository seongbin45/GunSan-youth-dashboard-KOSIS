from __future__ import annotations

import streamlit as st

from services.policy_loader import load_policies


st.set_page_config(page_title="FinFit", page_icon="💰", layout="wide")


def _init_state() -> None:
    st.session_state.setdefault("income", 2_000_000)
    st.session_state.setdefault("level", 5)
    st.session_state.setdefault("expenses", [])


def _route_query_param() -> None:
    routes = {
        "benefit": "pages/4_군산시민 맞춤 혜택 찾기.py",
        "finance": "pages/5_금융용어.py",
        "ai": "pages/2_AI와_대화하기.py",
        "ledger": "pages/Household_Ledger.py",
        "savings": "pages/Savings_Step_Setting_Guide.py",
        "policies": "pages/3_정부 지원 혜택 목록.py",
        "updates": "pages/7_청년혜택업데이트.py",
        "data": "pages/6_군산시 청년 데이터.py",
    }

    target = st.query_params.get("page")
    if target in routes:
        st.query_params.clear()
        st.switch_page(routes[target])


def _render_card(title: str, body: str, page: str, button_label: str) -> None:
    with st.container(border=True):
        st.subheader(title)
        st.write(body)
        if st.button(button_label, use_container_width=True, key=f"go-{page}"):
            st.switch_page(page)


_init_state()
_route_query_param()

policies = load_policies()

st.title("FinFit")
st.markdown("#### 사회초년생을 위한 청년 혜택 추천과 쉬운 금융 정보 MVP")

metric_cols = st.columns(3)
metric_cols[0].metric("관리 중인 정책", f"{len(policies)}개")
metric_cols[1].metric("MVP 범위", "3개 핵심 기능")
metric_cols[2].metric("정책 데이터", "JSON 기반")

st.divider()

st.markdown(
    """
FinFit v1은 기능을 더 붙이기보다, 이미 만든 기능을 운영 가능한 MVP 구조로 정리합니다.

1. 최신 청년 혜택을 업데이트 가능한 구조로 관리
2. 나에게 맞는 혜택 추천
3. 어려운 금융 정보를 쉬운 언어로 설명
"""
)

col1, col2, col3 = st.columns(3)
with col1:
    _render_card(
        "맞춤 혜택 추천",
        "나이, 소득, 고용 상태, 주거 조건을 입력하면 정책 데이터에서 1차 후보를 추천합니다.",
        "pages/4_군산시민 맞춤 혜택 찾기.py",
        "추천 받기",
    )
with col2:
    _render_card(
        "청년 혜택 업데이트",
        "공공 API 동기화, 데이터 신선도, 캐시 상태를 한 화면에서 확인합니다.",
        "pages/7_청년혜택업데이트.py",
        "운영 상태 보기",
    )
with col3:
    _render_card(
        "금융 용어 설명",
        "중위소득, 비과세, 매칭지원처럼 어려운 금융·정책 용어를 쉬운 말로 확인합니다.",
        "pages/5_금융용어.py",
        "용어 보기",
    )

st.divider()

quick_cols = st.columns(4)
with quick_cols[0]:
    st.page_link("pages/3_정부 지원 혜택 목록.py", label="정책 목록")
with quick_cols[1]:
    st.page_link("pages/6_군산시 청년 데이터.py", label="군산 청년 데이터")
with quick_cols[2]:
    st.page_link("pages/Savings_Step_Setting_Guide.py", label="저축 단계 가이드")
with quick_cols[3]:
    st.page_link("pages/Household_Ledger.py", label="가계부")

st.divider()

st.caption("FinFit은 금융상품 가입 대행, 법적 자격 판정, 투자 자문을 제공하지 않습니다.")
