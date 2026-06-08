from __future__ import annotations

import streamlit as st

from services.models import UserProfile
from services.policy_loader import load_policies
from services.recommendation import match_policies


st.set_page_config(page_title="군산시 청년 맞춤 혜택 찾기", page_icon="🎯", layout="wide")

INCOME_LEVELS = {
    "60% 이하": 60,
    "100% 이하": 100,
    "120% 이하": 120,
    "140% 이하": 140,
    "150% 이하": 150,
    "180% 이하": 180,
    "250% 이하": 250,
    "소득 기준 초과/모름": None,
}

EMPLOYMENT_STATUS = {
    "대학생/재학생": "student",
    "미취업/구직 중": "job_seeker",
    "취업자": "worker",
    "창업자": "founder",
    "농업 종사자": "farmer",
}


st.title("군산시 청년 맞춤 혜택 찾기")
st.caption("정책 조건은 UI 코드가 아니라 data/policies.json과 services/recommendation.py에서 관리합니다.")

with st.expander("어려운 용어를 먼저 쉽게 확인하기"):
    st.markdown(
        """
- **중위소득**: 정부 지원 기준을 정할 때 쓰는 소득 기준선입니다.
- **비과세**: 이자나 수익에 세금을 줄이거나 면제해 주는 혜택입니다.
- **매칭 지원**: 내가 저축한 금액에 정부나 지자체가 일정 금액을 더해 주는 방식입니다.
- **무주택**: 본인 명의 주택을 소유하지 않은 상태를 말합니다.
"""
    )

policies = load_policies()

with st.form("profile-form"):
    st.subheader("나의 조건")
    col1, col2, col3 = st.columns(3)
    age_value = col1.number_input("만 나이", min_value=15, max_value=69, value=25)
    income_label = col2.selectbox("가구 중위소득 기준", list(INCOME_LEVELS))
    employment_label = col3.selectbox("현재 상태", list(EMPLOYMENT_STATUS))

    col4, col5, col6 = st.columns(3)
    has_house_label = col4.radio("주택 소유 여부", ["무주택", "유주택"], horizontal=True)
    region = col5.selectbox("거주/활동 지역", ["군산시", "전북", "전국"], index=0)
    annual_income = col6.number_input("연소득(백만 원, 모르면 0)", min_value=0, max_value=200, value=0)

    all_keywords = sorted({keyword for policy in policies for keyword in policy.keywords})
    keywords = st.multiselect("관심 키워드", all_keywords, default=["청년"] if "청년" in all_keywords else [])
    submitted = st.form_submit_button("내 맞춤 혜택 결과 보기", use_container_width=True)

if submitted:
    profile = UserProfile(
        age=int(age_value),
        employment_status=EMPLOYMENT_STATUS[employment_label],
        has_house=has_house_label == "유주택",
        region=region,
        median_income_percent=INCOME_LEVELS[income_label],
        annual_income_million_krw=int(annual_income) or None,
        keywords=keywords,
    )
    matches = match_policies(profile, policies)

    st.success(f"총 {len(matches)}개 정책 후보를 찾았습니다.")
    for match in matches:
        policy = match.policy
        with st.expander(f"{policy.name} · {policy.category} · 점수 {match.score}"):
            st.write(policy.benefit)
            st.markdown(f"**추천 이유:** {', '.join(match.reasons)}")
            st.caption(f"출처: {policy.source} · 기준일: {policy.updated_at}")
            if policy.url:
                st.link_button("공식 출처 확인", policy.url)

    if not matches:
        st.info("현재 입력 조건과 일치하는 정책이 없습니다. 소득 기준을 모름으로 두거나 키워드를 줄여 다시 확인해보세요.")

st.caption("이 결과는 법적 자격 판정이 아니라 공식 출처 확인을 돕는 1차 추천입니다.")
