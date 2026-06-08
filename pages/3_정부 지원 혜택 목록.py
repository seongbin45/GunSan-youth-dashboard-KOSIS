from __future__ import annotations

import pandas as pd
import streamlit as st

from services.policy_loader import load_policies


st.set_page_config(page_title="청년 혜택 목록", page_icon="🎁", layout="wide")

st.title("청년 혜택 목록")
st.caption("정책 데이터는 data/policies.json에서 로딩됩니다. 정책 추가와 수정은 코드 변경 없이 데이터 중심으로 진행합니다.")

policies = load_policies()

categories = ["전체"] + sorted({policy.category for policy in policies})
selected_category = st.selectbox("분류", categories)
keyword = st.text_input("검색어", placeholder="예: 저축, 주거, 취업")

rows = []
for policy in policies:
    if selected_category != "전체" and policy.category != selected_category:
        continue
    searchable = " ".join([policy.name, policy.category, policy.benefit, " ".join(policy.keywords)])
    if keyword and keyword.lower() not in searchable.lower():
        continue
    rows.append(
        {
            "정책명": policy.name,
            "분류": policy.category,
            "혜택": policy.benefit,
            "출처": policy.source,
            "기준일": policy.updated_at,
        }
    )

st.metric("조회 정책 수", f"{len(rows)}개")

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.warning("검색 조건에 맞는 정책이 없습니다.")

for policy in policies:
    if selected_category != "전체" and policy.category != selected_category:
        continue
    searchable = " ".join([policy.name, policy.category, policy.benefit, " ".join(policy.keywords)])
    if keyword and keyword.lower() not in searchable.lower():
        continue
    with st.expander(policy.name):
        st.write(policy.benefit)
        st.markdown(f"**대상 연령:** {policy.eligibility.age_min or '제한 없음'} ~ {policy.eligibility.age_max or '제한 없음'}")
        st.markdown(f"**상태 조건:** {', '.join(policy.eligibility.employment_status) or '제한 없음'}")
        st.markdown(f"**지역:** {', '.join(policy.eligibility.regions) or '제한 없음'}")
        st.caption(f"출처: {policy.source} · 기준일: {policy.updated_at}")
        if policy.url:
            st.link_button("공식 출처 확인", policy.url)
