"""
군산시 청년 맞춤 혜택 찾기

Single matching path: finfit_youth.benefits_matcher (온통청년 policy cache
synced by pages/7_청년혜택업데이트.py) — same source as AI check_benefit_eligibility.
"""
import streamlit as st
import textwrap

from finfit_youth.config import inject_finfit_theme
from finfit_youth.benefits_matcher import match_benefits_for_ui, load_policy_snapshot
from finfit_youth.trust_copy import benefits_trust_markdown, policy_cache_meta

st.set_page_config(page_title="군산시 청년 맞춤 혜택 찾기", page_icon="🎁", layout="wide")
inject_finfit_theme()

st.markdown(
    """
<style>
.stApp { background: #111111 !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    textwrap.dedent(
        """
<div style="background:#1a1a1a; padding:12px 16px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div>
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">🎁 군산시 청년 맞춤 혜택 찾기</div>
      <div style="font-size:12px;color:#888;">온통청년 정책 캐시 기반 · AI 상담과 동일한 매칭 엔진</div>
    </div>
  </div>
</div>
"""
    ),
    unsafe_allow_html=True,
)

# --- session defaults from onboarding / other pages ---
default_age = 25
default_income_ui = "100% 이하"
default_emp = "미취업 (구직 중)"
default_house = "무주택"

# Prefer explicit profile if user already matched once
if st.session_state.get("benefit_profile"):
    bp = st.session_state.benefit_profile
    default_age = int(bp.get("age") or default_age)
    default_income_ui = bp.get("income_ui") or default_income_ui
    default_emp = bp.get("employment_ui") or default_emp
    default_house = bp.get("housing_ui") or default_house
else:
    # soft link: onboarding range string → select option
    rng = str(st.session_state.get("monthly_income_range") or "")
    if "60" in rng:
        default_income_ui = "60% 이하 (저소득층 및 집중 주거지원 대상)"
    elif "150" in rng or "140" in rng:
        default_income_ui = "140% 이하"
    elif "180" in rng or "200" in rng:
        default_income_ui = "180% 이하"

_cm = policy_cache_meta()
cache_n = _cm["cache_size"]
if cache_n == 0:
    st.warning(
        "온통청년 정책 캐시가 비어 있습니다. "
        "**청년혜택업데이트** 페이지에서 정책을 동기화하면 실데이터가 반영됩니다. "
        "지금은 로컬 폴백 목록이 사용될 수 있습니다."
    )
else:
    st.caption(
        f"📦 정책 캐시: **{cache_n:,}**건 · 갱신 {_cm['cache_age_text']} "
        f"(youth_cache · 7_청년혜택업데이트 동기화)"
    )

with st.expander("⚠️ 매칭 결과의 의미·한계 (필독)", expanded=False):
    st.markdown(benefits_trust_markdown({"cache_size": cache_n, "cache_age_text": _cm["cache_age_text"]}))

income_options = [
    "60% 이하 (저소득층 및 집중 주거지원 대상)",
    "100% 이하",
    "140% 이하",
    "150% 이하",
    "180% 이하",
    "해당 없음 (소득 기준 초과)",
]
keyword_options = [
    "미취업 (구직 중)",
    "취업자 (군산 소재 기업)",
    "창업자 (7년 미만)",
    "농업 종사 (청년창업농 등)",
    "신혼부부",
    "다자녀 가구",
]

with st.form("benefit_match_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("만 나이", min_value=15, max_value=69, value=int(default_age))
    with c2:
        income_level = st.selectbox(
            "가구 소득 수준",
            income_options,
            index=income_options.index(default_income_ui)
            if default_income_ui in income_options
            else 1,
        )
    with c3:
        has_house = st.radio(
            "주택 소유",
            ["무주택", "유주택"],
            index=0 if default_house == "무주택" else 1,
            horizontal=True,
        )

    selected_keywords = st.multiselect(
        "해당하는 조건 (복수 선택)",
        options=keyword_options,
        default=[default_emp] if default_emp in keyword_options else [keyword_options[0]],
    )
    query_extra = st.text_input(
        "추가 검색어 (선택)",
        placeholder="예: 월세, 적금, 취업, 전북",
        help="온통청년 정책 제목·요약 가중 검색",
    )
    submitted = st.form_submit_button("🔍 맞춤 혜택 매칭 (온통청년 캐시)", use_container_width=True)

if submitted:
    result = match_benefits_for_ui(
        age=int(age),
        income_level=income_level,
        has_house=has_house,
        selected_keywords=selected_keywords,
        query=query_extra,
        limit=20,
    )
    st.session_state.matched = result.get("matched_policies") or []
    st.session_state.matched_benefit_cards = result.get("benefits") or []
    st.session_state.benefit_match_meta = {
        "data_source": result.get("data_source"),
        "cache_size": result.get("cache_size"),
        "cache_age_text": result.get("cache_age_text"),
        "is_fallback": result.get("is_fallback"),
        "summary": result.get("summary"),
        "disclaimer": result.get("disclaimer"),
        "method": result.get("method"),
        "normalized": result.get("normalized"),
    }
    st.session_state.benefit_profile = {
        "age": int(age),
        "income_ui": income_level,
        "housing_ui": has_house,
        "employment_ui": (selected_keywords[0] if selected_keywords else default_emp),
        "keywords": selected_keywords,
    }
    # Canonical UserContext snapshot (same schema AI agent reads)
    try:
        from finfit_youth.user_context import build_user_context, write_context_to_session

        _ctx = build_user_context(st.session_state)
        write_context_to_session(st.session_state, _ctx)
        st.caption(
            f"프로필 반영: age={_ctx.age}, income_level={_ctx.income_level}, "
            f"employment={_ctx.employment_status}, house={_ctx.has_house} "
            f"(출처: benefit_profile)"
        )
    except Exception:
        pass
    st.success(
        f"매칭 {result.get('matched_count', 0)}건 · 출처: {result.get('data_source', '-')}"
    )
    if result.get("is_fallback"):
        st.warning("로컬 폴백 목록입니다. 공식 자격·전체 정책이 아닙니다. 7페이지에서 캐시를 동기화하세요.")
    else:
        st.info(result.get("disclaimer") or "")

# --- results ---
cards = st.session_state.get("matched_benefit_cards") or []
meta = st.session_state.get("benefit_match_meta") or {}
names = st.session_state.get("matched") or []

# category filter (map matcher categories → UI tabs)
CAT_MAP = {
    "전체": None,
    "금융": ("자산형성", "금융"),
    "주거": ("주거",),
    "취업": ("구직", "일자리", "취업"),
    "교육": ("교육",),
    "생활": ("생활복지", "복지", "생활"),
}
active = st.radio("카테고리", list(CAT_MAP.keys()), horizontal=True, label_visibility="collapsed")

if not cards and not names:
    st.info("위에서 조건을 입력하고 **맞춤 혜택 매칭**을 눌러주세요. AI 대화 페이지와 같은 엔진·같은 캐시를 사용합니다.")
else:
    if meta:
        st.caption(meta.get("summary") or "")
        if meta.get("disclaimer"):
            st.caption(f"⚠️ {meta['disclaimer']}")
        if meta.get("cache_age_text") is not None:
            st.caption(
                f"출처 `{meta.get('data_source')}` · 캐시 {meta.get('cache_size', '?')}건 · "
                f"갱신 {meta.get('cache_age_text')} · "
                f"{'폴백' if meta.get('is_fallback') else '캐시 매칭'}"
            )
    st.markdown(f"### 📋 매칭 결과 ({len(cards) or len(names)}건) — 추천 순위, 확정 자격 아님")

    shown = 0
    for b in cards:
        cat = str(b.get("category") or "")
        want = CAT_MAP.get(active)
        if want and not any(w in cat for w in want):
            # also allow keyword in title for broad cats
            title = str(b.get("name") or "")
            if active == "금융" and not any(k in title + cat for k in ("금융", "적금", "저축", "자산")):
                continue
            if active == "주거" and not any(k in title + cat for k in ("주거", "월세", "전세", "주택")):
                continue
            if active == "취업" and not any(k in title + cat for k in ("취업", "구직", "일자리")):
                continue
            if active not in ("금융", "주거", "취업") and want and not any(w in cat for w in want):
                continue

        name = b.get("name") or "제목 없음"
        benefit = b.get("benefit") or ""
        condition = b.get("condition") or ""
        region = b.get("region_match") or ""
        url = b.get("url") or ""
        source = b.get("source") or ""
        pid = b.get("policy_id") or ""

        with st.container():
            st.markdown(
                f"""
<div style="background:#1a1a1a;border:1px solid #333;border-radius:14px;padding:14px 16px;margin-bottom:10px;">
  <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;">
    <div>
      <span style="background:#EEF0FF;color:#111;font-size:10px;padding:2px 6px;border-radius:4px;">{cat or "청년정책"}</span>
      <span style="background:#222;color:#10B981;font-size:10px;padding:2px 6px;border-radius:4px;margin-left:4px;">매칭</span>
      <div style="font-weight:700;color:#f0f0f0;font-size:15px;margin-top:6px;">{name}</div>
      <div style="color:#aaa;font-size:12px;margin-top:4px;">{benefit[:220]}</div>
      <div style="color:#888;font-size:11px;margin-top:6px;">조건: {condition}</div>
      <div style="color:#666;font-size:10px;margin-top:4px;">{region} · {source}{(" · " + pid) if pid else ""}</div>
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            if url:
                st.markdown(f"[신청/참고 링크]({url})")
            shown += 1

    if cards and shown == 0:
        st.warning("이 카테고리 필터에 해당하는 항목이 없습니다. **전체**를 선택해 보세요.")

    # legacy name-only fallback
    if not cards and names:
        for n in names:
            st.markdown(f"- **{n}**")

st.divider()
st.markdown(benefits_trust_markdown(meta if meta else None))
st.caption(
    "엔진: `benefits_matcher` · AI `check_benefit_eligibility`와 동일 · "
    "동기화: **청년혜택업데이트**"
)

# Bridge for AI: keep latest match in session (Agent.sync_from_session reads these)
if st.session_state.get("matched_benefit_cards"):
    st.session_state["ai_shared_benefits"] = st.session_state["matched_benefit_cards"]
