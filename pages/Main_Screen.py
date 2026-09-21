import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap
from finfit_youth.config import inject_finfit_theme, LEVELS

st.set_page_config(page_title="FinFit - Overview", page_icon="💰", layout="wide")
inject_finfit_theme()

st.markdown("""
<style>
.stApp { background: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# Consistent header
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div>
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">💰 FinFit - 머니 플래너</div>
      <div style="font-size:12px;color:#888;">금융 미경험 청년을 위한 AI 기반 정부혜택 자동 매칭 플랫폼</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">📋 기본 정보 입력</b></div>', unsafe_allow_html=True)
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=10000, max_value=10000000,
        value=int(st.session_state.income), step=100000,
        format="%d",
    )
    if int(income) != int(st.session_state.get("income") or 0):
        st.session_state.income_touched = True
    st.session_state.income = int(income)

    st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">🎚️ 저축 강도 선택 (1~10단계)</b></div>', unsafe_allow_html=True)
    level = st.slider(
        "1 = 여가 최우선 ~ 10 = 생존형 저축",
        min_value=1, max_value=10,
        value=st.session_state.level
    )
    st.session_state.level = level

    lv = LEVELS[level]
    st.markdown(f"""
    <div style="background:{lv['color']}22; border-left:5px solid {lv['color']};
                padding:14px 18px; border-radius:8px; margin-top:10px; background:#1a1a1a;">
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


st.subheader("📢 군산시 청년 맞춤 혜택 (요약 뷰)")
st.caption(
    "온통청년 정책 캐시 기반 · **4_맞춤 혜택 찾기** · **AI 상담**과 동일한 `benefits_matcher` 엔진. "
    "상세 카드·필터는 4번 페이지를 이용하세요. **추천 순위 ≠ 신청 가능 확정.**"
)

from finfit_youth.benefits_matcher import match_benefits_for_ui, load_policy_snapshot
from finfit_youth.trust_copy import benefits_trust_markdown, policy_cache_meta

_cm = policy_cache_meta()
_cache_n = _cm["cache_size"]
if _cache_n == 0:
    st.warning("정책 캐시가 비어 있습니다. **청년혜택업데이트**에서 정책을 동기화하면 실데이터가 반영됩니다.")
else:
    st.caption(f"📦 정책 캐시 {_cache_n:,}건 · 갱신 {_cm['cache_age_text']}")
with st.expander("⚠️ 매칭 의미·한계", expanded=False):
    st.markdown(benefits_trust_markdown({"cache_size": _cache_n, "cache_age_text": _cm["cache_age_text"]}))

with st.expander("핵심 용어 간단 정리", expanded=False):
    st.markdown(
        """
- **중위소득 %**: 지원 자격의 소득 기준선  
- **매칭 지원**: 내가 저축하면 지자체가 같은 금액을 더 주는 방식  
- **비과세**: 이자에 세금이 거의 안 붙는 혜택  
- 정책 본문은 온통청년 공고·링크를 기준으로 확인하세요.
"""
    )

_income_opts = [
    "60% 이하 (저소득층 및 집중 주거지원 대상)",
    "100% 이하",
    "140% 이하",
    "150% 이하",
    "180% 이하",
    "해당 없음 (소득 기준 초과)",
]
_kw_opts = [
    "미취업 (구직 중)",
    "취업자 (군산 소재 기업)",
    "창업자 (7년 미만)",
    "농업 종사 (청년창업농 등)",
    "신혼부부",
    "다자녀 가구",
]

with st.form("main_benefit_match_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("만 나이", min_value=15, max_value=69, value=25, key="main_age")
    with c2:
        income_level = st.selectbox("가구 소득 수준", _income_opts, index=1, key="main_income")
    with c3:
        has_house = st.radio("주택 소유", ["무주택", "유주택"], horizontal=True, key="main_house")
    selected_keywords = st.multiselect(
        "해당 조건",
        options=_kw_opts,
        default=["미취업 (구직 중)"],
        key="main_keywords",
    )
    main_query = st.text_input("추가 검색어 (선택)", placeholder="예: 월세, 적금, 취업", key="main_q")
    main_submit = st.form_submit_button("맞춤 혜택 매칭 (온통청년 캐시)", use_container_width=True)

if main_submit:
    _res = match_benefits_for_ui(
        age=int(age),
        income_level=income_level,
        has_house=has_house,
        selected_keywords=selected_keywords,
        query=main_query,
        limit=12,
    )
    st.session_state["main_matched_cards"] = _res.get("benefits") or []
    st.session_state["matched"] = _res.get("matched_policies") or []
    st.session_state["matched_benefit_cards"] = _res.get("benefits") or []
    st.session_state["ai_shared_benefits"] = _res.get("benefits") or []
    st.session_state["benefit_profile"] = {
        "age": int(age),
        "income_ui": income_level,
        "housing_ui": has_house,
        "employment_ui": (selected_keywords[0] if selected_keywords else "미취업 (구직 중)"),
        "keywords": selected_keywords,
    }
    try:
        from finfit_youth.user_context import build_user_context, write_context_to_session

        write_context_to_session(st.session_state, build_user_context(st.session_state))
    except Exception:
        pass
    st.session_state["benefit_match_meta"] = {
        "data_source": _res.get("data_source"),
        "cache_size": _res.get("cache_size"),
        "cache_age_text": _res.get("cache_age_text"),
        "is_fallback": _res.get("is_fallback"),
        "summary": _res.get("summary"),
        "disclaimer": _res.get("disclaimer"),
        "method": _res.get("method"),
    }
    st.success(f"매칭 {_res.get('matched_count', 0)}건 · {_res.get('data_source', '')}")
    if _res.get("is_fallback"):
        st.warning("로컬 폴백 목록입니다. 7페이지에서 정책 캐시를 동기화하세요.")
    elif _res.get("disclaimer"):
        st.caption(f"⚠️ {_res['disclaimer']}")

_cards = st.session_state.get("main_matched_cards") or st.session_state.get("matched_benefit_cards") or []
if _cards:
    st.markdown(f"### 매칭 결과 (상위 {min(8, len(_cards))}건 미리보기) — 확정 자격 아님")
    if st.session_state.get("benefit_match_meta"):
        _bm = st.session_state["benefit_match_meta"]
        st.caption(_bm.get("summary") or "")
        if _bm.get("disclaimer"):
            st.caption(f"⚠️ {_bm['disclaimer']}")
    for b in _cards[:8]:
        name = b.get("name") or "제목 없음"
        cat = b.get("category") or "청년정책"
        benefit = (b.get("benefit") or "")[:180]
        condition = b.get("condition") or ""
        url = b.get("url") or ""
        with st.expander(f"📌 {name}  [{cat}]"):
            st.write(benefit)
            st.caption(f"조건: {condition}")
            st.caption(f"{b.get('region_match') or ''} · {b.get('source') or ''}")
            if url:
                st.markdown(f"[신청/참고 링크]({url})")
    st.info(
        "전체 필터·상세 보기는 사이드바 **군산시민 맞춤 혜택 찾기(4번)** 페이지를 이용하세요. "
        "AI 상담과 같은 매칭 결과가 세션에 공유됩니다."
    )
else:
    st.caption(
        "조건을 입력하고 매칭 버튼을 누르면, 4번 페이지·AI와 동일한 온통청년 캐시 결과가 표시됩니다."
    )

st.write("---")

# ── 군산 통계 요약: page 6 · AI 와 동일 gunsan_stats (raw SQL / 하드코딩 금지) ──
from finfit_youth.gunsan_stats import (
    get_gunsan_stat,
    load_dashboard_data,
    DASHBOARD_TABLES,
)
from finfit_youth.trust_copy import stats_trust_markdown, stats_provenance
from finfit_youth.kosis_sync import core_freshness_status

st.subheader("📊 군산시 청년 데이터 (요약)")
st.caption(
    "6_군산시 청년 데이터 · AI `get_gunsan_youth_stats` 와 동일한 "
    "`finfit_youth.gunsan_stats` 경로. 추정 수치로 채우지 않습니다. "
    "전체 차트·동기화는 **군산시 청년 데이터** 페이지를 이용하세요."
)

_fresh = core_freshness_status()
if _fresh["stale"]:
    st.warning(_fresh["summary"] + " · 갱신은 **군산시 청년 데이터** 페이지에서.")
else:
    st.caption(_fresh["summary"])

_prov = stats_provenance()
with st.expander("⚠️ 통계 출처·한계", expanded=False):
    st.markdown(stats_trust_markdown(_prov))


@st.cache_data
def _main_load_stats():
    return load_dashboard_data()


try:
    bundle = _main_load_stats()
    tables = bundle.get("tables") or {}
    house_df = tables.get("housing", pd.DataFrame())
    wage_df = tables.get("wage", pd.DataFrame())
    health_df = tables.get("health", pd.DataFrame())

    st.caption(
        f"DB: `{bundle.get('db_path')}` · "
        f"테이블 {len(DASHBOARD_TABLES) - len(bundle.get('missing') or [])}/{len(DASHBOARD_TABLES)} · "
        f"KOSIS 핵심 동기화 {_prov.get('core_sync_age_text')}"
    )
    if not bundle.get("ok"):
        st.error(f"DB를 찾을 수 없습니다: {bundle.get('db_path')}")
    if bundle.get("missing"):
        st.warning("일부 표 없음: " + ", ".join(bundle["missing"]))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**1. 청년 인구**")
        _pop = get_gunsan_stat("population")
        st.caption(_pop.get("source") or "")
        _figp = _pop.get("figures") or {}
        youth_raw = _figp.get("gunsan_youth_18_39")
        total_raw = _figp.get("gunsan_total_approx")
        if _pop.get("from_db") and youth_raw is not None:
            st.metric("군산 청년(18~39세)", f"{int(youth_raw):,}명")
            if total_raw is not None and int(total_raw) > int(youth_raw):
                pie_data = pd.DataFrame(
                    {
                        "구분": ["청년 인구(18~39세)", "그 외 인구"],
                        "인구수": [int(youth_raw), int(total_raw) - int(youth_raw)],
                    }
                )
                fig1 = px.pie(
                    pie_data,
                    values="인구수",
                    names="구분",
                    title="시 전체 대비 청년 비율",
                    color_discrete_sequence=["#FF6B6B", "#555"],
                )
                st.plotly_chart(fig1, width="stretch", key="main_fig_pop")
            else:
                st.info("전체 인구 합계 표가 없어 비중 파이차트는 생략합니다 (추정 금지).")
                if _pop.get("data"):
                    st.write(_pop["data"])
        else:
            st.warning(_pop.get("data") or "인구 요약을 DB에서 읽지 못했습니다.")

    with col_b:
        st.markdown("**2. 주택 소유 비율**")
        _h = get_gunsan_stat("housing")
        if _h.get("source"):
            st.caption(_h["source"])
        if house_df is None or house_df.empty or "C2_NM" not in house_df.columns:
            st.warning("주택 표를 불러오지 못했습니다.")
            if _h.get("from_db") and _h.get("data"):
                st.write(_h["data"])
        else:
            house_ratio = house_df[house_df["C2_NM"].str.contains("비율", na=False)].copy()
            house_ratio["DT"] = pd.to_numeric(house_ratio["DT"], errors="coerce")
            latest_year = house_ratio["PRD_DE"].max()
            latest_house = house_ratio[house_ratio["PRD_DE"] == latest_year]
            fig2 = px.bar(
                latest_house,
                x="C1_NM",
                y="DT",
                text="DT",
                title=f"{latest_year}년 연령대별 주택 소유 비율",
                labels={"C1_NM": "구분", "DT": "소유 비율(%)"},
                color="C1_NM",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig2.update_traces(texttemplate="%{text}%", textposition="outside")
            st.plotly_chart(fig2, width="stretch", key="main_fig_house")

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**3. 소득(임금) 구간**")
        _inc = get_gunsan_stat("income")
        if _inc.get("source"):
            st.caption(_inc["source"])
        if wage_df is None or wage_df.empty or "DT" not in wage_df.columns:
            st.warning("임금 표를 불러오지 못했습니다.")
            if _inc.get("from_db") and _inc.get("data"):
                st.write(_inc["data"])
        else:
            wage_plot = wage_df.copy()
            wage_plot["DT"] = pd.to_numeric(wage_plot["DT"], errors="coerce")
            ly = wage_plot["PRD_DE"].max()
            latest_wage = wage_plot[wage_plot["PRD_DE"] == ly]
            fig3 = px.bar(
                latest_wage,
                x="C2_NM",
                y="DT",
                color="C1_NM",
                title=f"{ly}년 소득 구간별 인구",
                labels={"C2_NM": "소득 구간", "DT": "인구(천명)"},
                barmode="group",
            )
            st.plotly_chart(fig3, width="stretch", key="main_fig_wage")

    with col_d:
        st.markdown("**4. AI와 동일 요약 문장**")
        for cat, label in (
            ("employment_difficulty", "취업 어려움(군산 %)"),
            ("employment_count", "취업자 수(전북 분기평균)"),
            ("population", "인구"),
        ):
            r = get_gunsan_stat(cat)
            st.markdown(f"**{label}** · `{cat}` · from_db={r.get('from_db')}")
            st.caption((r.get("data") or "")[:320])

    if health_df is not None and not health_df.empty and "DT" in health_df.columns:
        with st.expander("건강 지표 미리보기 (gunsan_youth_health_data)"):
            hp = health_df.copy()
            hp["DT"] = pd.to_numeric(hp["DT"], errors="coerce")
            st.dataframe(hp.head(12), width="stretch")

    st.info(
        "원룸·취업 상세 차트·KOSIS 동기화는 사이드바 **군산시 청년 데이터** 페이지에 있습니다. "
        "Main은 요약만 표시해 6페이지·AI와 숫자가 어긋나지 않게 합니다."
    )

except FileNotFoundError as e:
    st.error(f"DB 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"통계 요약 표시 중 오류: {e}")
