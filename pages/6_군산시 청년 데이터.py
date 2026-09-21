import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap
from finfit_youth.config import inject_finfit_theme, render_feedback_form

st.set_page_config(page_title="군산시 청년 데이터", page_icon="📊", layout="wide")
inject_finfit_theme()

# Force dark background for consistency
st.markdown("""
<style>
.stApp { background: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# Consistent header like other pages (dark theme, TSX style)
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div onclick="window.history.back()" style="width:36px;height:36px;background:#222;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;">
      <span style="font-size:18px;color:#aaa;">←</span>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">📊 군산시 청년 데이터</div>
      <div style="font-size:12px;color:#888;">KOSIS 기반 인구·주거·소득·건강 지표. 키·동기화 실패 시에도 로컬 DB 차트는 유지됩니다.</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

st.markdown("""
<div style="background:#1a1a1a; border:1px solid #333; border-radius:12px; padding:14px; margin:8px 0;">
  <b style="color:#f0f0f0;">📅 데이터 기준:</b> KOSIS 공표 연도 (표마다 상이, 보통 조사 후 1~2년 시차)<br>
  <b style="color:#f0f0f0;">🏢 데이터 출처:</b> 국가통계포털(KOSIS) · 로컬 DB <code>gunsan_youth_data.db</code><br>
  <b style="color:#f0f0f0;">🔗 AI 연동:</b> 차트·요약·AI 통계 툴이 모두 <code>finfit_youth.gunsan_stats</code> 단일 경로<br>
  <b style="color:#f0f0f0;">⚠️ 정확성:</b> DB에 없는 수치는 추정으로 채우지 않습니다. 표마다 조사 연도(PRD_DE)가 다를 수 있습니다.<br>
  <b style="color:#888;">💡 유지보수:</b> 아래 버튼 또는 <code>KOSIS_Database_Creation_Code/make_database.py</code> 로 KOSIS에서 재수집
</div>
""", unsafe_allow_html=True)

# --- KOSIS 자동 갱신 (문서 4_&_5_pages 파이프라인) ---
from finfit_youth.kosis_sync import (
    last_core_sync_age_seconds,
    needs_core_sync,
    ensure_fresh_core,
    sync_core_tables,
    sync_all,
    core_freshness_status,
)
from finfit_youth.config import (
    KOSIS_API_KEY,
    GUNSAN_STATS_DB_PATH,
    GUNSAN_STATS_SYNC_TTL_SECONDS,
    secret_status,
)

# ── KOSIS key + freshness (page never stops; DB charts still load) ──
try:
    ks = secret_status("KOSIS_API_KEY")
except Exception:
    ks = {"configured": False, "source": None, "masked": ""}
_has_kosis_key = bool(ks.get("configured")) or bool((KOSIS_API_KEY or "").strip())
try:
    _fresh = core_freshness_status()
except Exception as _fresh_err:
    _fresh = {
        "stale": False,
        "summary": f"신선도 상태 확인 실패: {_fresh_err}",
        "db_exists": None,
    }
_fresh_stale = bool(_fresh.get("stale"))

if _has_kosis_key:
    st.success(
        f"KOSIS_API_KEY 설정됨 · 출처 `{ks.get('source') or 'env'}` · "
        f"`{ks.get('masked') or '***'}` · 필요 시 아래에서 동기화할 수 있습니다."
    )
else:
    st.warning(
        "⚠️ **KOSIS_API_KEY 가 없습니다.** 페이지는 열리며 "
        f"**로컬 DB (`{GUNSAN_STATS_DB_PATH}`)** 차트·AI 통계 툴은 계속 동작합니다. "
        "신규 KOSIS 수집·갱신만 키가 필요합니다. "
        "배포/로컬 모두 `.streamlit/secrets.toml` 또는 환경변수에 키를 넣으세요."
    )

if _fresh_stale:
    st.info(
        _fresh.get("summary")
        + " · 키가 있으면 아래 유지보수에서 **TTL 필요 시만 갱신** 또는 핵심 동기화를 실행하세요."
        + (" (현재 키 없음 — DB 기존 데이터로 표시)" if not _has_kosis_key else "")
    )
else:
    st.caption(_fresh.get("summary") or "신선도 상태 확인됨")

with st.expander(
    "🔄 KOSIS 데이터 갱신 (유지보수)",
    expanded=(not _has_kosis_key) or _fresh_stale,
):
    if _has_kosis_key:
        st.write(
            f"- **KOSIS_API_KEY**: 설정됨 · 출처 `{ks.get('source') or 'env'}` · "
            f"`{ks.get('masked') or '***'}`"
        )
    else:
        st.write("- **KOSIS_API_KEY**: **미설정**")
        st.markdown(
            """
**키 넣는 방법 (택 1)**

1. **가장 쉬움 (권장)** — 프로젝트 루트에서 터미널:
   ```bash
   python scripts/set_kosis_key.py
   ```
   키를 붙여넣으면 `.streamlit/secrets.toml` 에 저장됩니다.  
   CLI 동기화도 쓰려면: `python scripts/set_kosis_key.py --also-env`

2. **직접 편집** — `.streamlit/secrets.toml.example` 을 참고해  
   `.streamlit/secrets.toml` 에 한 줄 추가:
   ```toml
   KOSIS_API_KEY = "발급받은키"
   ```

3. **환경변수 / `.env`**
   ```bash
   copy .env.example .env
   # .env 안에 KOSIS_API_KEY=... 입력
   ```

**키 발급:** [KOSIS OpenAPI 신청](https://kosis.kr/openapi/sw/devInfo/OpenApiRequest.do)  
설정 후 **Streamlit을 한 번 재시작**하세요.  
상태 확인: `python scripts/set_kosis_key.py --status`
"""
        )

    age = last_core_sync_age_seconds()
    if age is None:
        st.caption(
            f"DB: `{GUNSAN_STATS_DB_PATH}` · 핵심표 자동동기화 기록 없음 "
            f"(기존 수동 적재·시드 DB 가능) · exists={_fresh.get('db_exists')}"
        )
    else:
        st.caption(
            f"DB: `{GUNSAN_STATS_DB_PATH}` · 마지막 핵심 동기화 약 {age // 3600}시간 전 · "
            f"TTL 초과(needs_core_sync)={needs_core_sync()}"
        )

    if not _has_kosis_key:
        st.caption(
            "키가 없으면 동기화 버튼은 스킵/안내만 하고, 아래 차트는 기존 DB로 그립니다. "
            "(st.stop 없음)"
        )

    def _sync_fail_message(exc: BaseException) -> str:
        msg = str(exc)
        low = msg.lower()
        if (
            "not set" in low
            or "api_key" in low
            or "kosis_api_key" in low
            or "KOSIS_API_KEY" in msg
        ):
            return (
                f"동기화 실패: KOSIS API 키가 없거나 비어 있습니다. ({exc})\n\n"
                "secrets/환경변수 설정 후 재시작하세요. "
                "기존 `gunsan_youth_data.db` 가 있으면 아래 차트는 계속 볼 수 있습니다."
            )
        return f"동기화 실패: {exc}"

    # ensure_fresh: only hits API when stale + key present (safe helper)
    if st.button("TTL 필요 시에만 핵심 갱신 (ensure_fresh_core)", use_container_width=True):
        try:
            with st.spinner("TTL 확인 후 필요 시 KOSIS 핵심 표 수집..."):
                result = ensure_fresh_core()
            if result.get("skipped"):
                reason = str(result.get("reason") or "")
                if "not set" in reason.lower() or "KOSIS_API_KEY" in reason:
                    st.warning(
                        "스킵: KOSIS_API_KEY 미설정. "
                        "기존 DB 차트는 그대로 표시됩니다. 키 설정 후 다시 시도하세요."
                    )
                else:
                    st.info(
                        f"스킵: {reason} · age={result.get('age_seconds')}"
                    )
            elif result.get("ok"):
                st.success(f"갱신 완료: {result.get('tables')}")
                st.cache_data.clear()
            else:
                err = result.get("error") or result
                st.error(
                    f"갱신 실패/부분 실패: {err}\n\n"
                    "페이지·차트는 유지됩니다. 네트워크/키 권한을 확인하세요."
                )
        except Exception as e:
            st.error(_sync_fail_message(e))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("핵심 표만 동기화 (인구·주택·임금·건강)", use_container_width=True):
            try:
                with st.spinner("KOSIS 핵심 표 수집 중..."):
                    result = sync_core_tables()
                if result.get("ok"):
                    st.success(f"완료: {result.get('tables')}")
                    st.cache_data.clear()
                else:
                    st.error(
                        f"일부 실패: {result}\n\n"
                        "이미 적재된 표는 아래에서 계속 표시됩니다."
                    )
            except Exception as e:
                st.error(_sync_fail_message(e))
    with c2:
        if st.button("전체 동기화 (목록 카탈로그 + 핵심 표)", use_container_width=True):
            try:
                with st.spinner("KOSIS 목록·수치 전체 수집 중..."):
                    result = sync_all()
                if result.get("ok"):
                    st.success("전체 동기화 완료")
                    st.json(result)
                    st.cache_data.clear()
                else:
                    st.error(
                        f"일부 실패: {result}\n\n"
                        "이미 적재된 표는 아래에서 계속 표시됩니다."
                    )
            except Exception as e:
                st.error(_sync_fail_message(e))
    st.caption(
        "과정 원본: Technical_document/.../4_&_5_pages.txt "
        "→ statisticsList(V_3_214_005) → statisticsParameterData(orgId=712, DT_712005_…) · "
        f"TTL 기본값 GUNSAN_STATS_SYNC_TTL_SECONDS={GUNSAN_STATS_SYNC_TTL_SECONDS} · "
        "자동 네트워크 호출 없음(버튼만)"
    )

st.write("---")

# 단일 데이터 경로: finfit_youth.gunsan_stats
# (AI 툴 get_gunsan_youth_stats 와 동일 DB · 동일 테이블 상수)
from finfit_youth.gunsan_stats import (
    get_gunsan_stat,
    load_dashboard_data,
    resolve_db_path,
    DASHBOARD_TABLES,
)
from finfit_youth.trust_copy import stats_trust_markdown, stats_provenance


@st.cache_data
def load_data():
    """Page charts only — no page-local sqlite/SQL."""
    return load_dashboard_data()


try:
    bundle = load_data()
    tables = bundle.get("tables") or {}
    house_df = tables.get("housing", pd.DataFrame())
    wage_df = tables.get("wage", pd.DataFrame())
    health_df = tables.get("health", pd.DataFrame())
    difficulty_df = tables.get("difficulty", pd.DataFrame())
    room_df = tables.get("room", pd.DataFrame())
    saving_df = tables.get("saving", pd.DataFrame())
    job_df = tables.get("job", pd.DataFrame())

    _prov = stats_provenance()
    st.caption(
        f"데이터 경로: `{bundle.get('db_path')}` · "
        f"로드 테이블 {len(DASHBOARD_TABLES) - len(bundle.get('missing') or [])}"
        f"/{len(DASHBOARD_TABLES)} · AI 통계 툴과 동일 모듈 · "
        f"KOSIS 핵심 동기화 {_prov.get('core_sync_age_text')}"
    )
    with st.expander("⚠️ 통계 출처·한계 (필독)", expanded=False):
        st.markdown(stats_trust_markdown(_prov))
    if bundle.get("missing"):
        st.warning(
            "일부 표가 DB에 없습니다: "
            + ", ".join(bundle["missing"])
            + " — 해당 차트는 비우거나 경고만 표시합니다 (추정 수치 사용 안 함)."
        )
    if not bundle.get("ok"):
        st.error(f"DB 파일을 찾을 수 없습니다: {bundle.get('db_path')}")

    # 📌 1 & 2번 영역
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">📌 1. 군산시 청년 인구 비중</b></div>', unsafe_allow_html=True)
        # AI tool 과 동일: get_gunsan_stat("population") — 하드코딩 인구 수치 사용 금지
        _pop = get_gunsan_stat("population")
        _fig = _pop.get("figures") or {}
        st.caption(_pop.get("source") or str(resolve_db_path()))
        youth_raw = _fig.get("gunsan_youth_18_39")
        total_raw = _fig.get("gunsan_total_approx")
        if _pop.get("from_db") and youth_raw is not None:
            youth_gunsan_pop = int(youth_raw)
            st.metric("군산 청년(18~39세)", f"{youth_gunsan_pop:,}명")
            if total_raw is not None and int(total_raw) > youth_gunsan_pop:
                total_gunsan_pop = int(total_raw)
                other_pop = total_gunsan_pop - youth_gunsan_pop
                pie_data = pd.DataFrame({
                    "구분": ["청년 인구(18~39세)", "그 외 인구"],
                    "인구수": [youth_gunsan_pop, other_pop],
                })
                fig1 = px.pie(
                    pie_data, values="인구수", names="구분",
                    title="군산시 전체 인구 대비 청년 비율",
                    color_discrete_sequence=["#FF6B6B", "#555"],
                )
                fig1.update_layout(template="plotly_dark", paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a")
                st.plotly_chart(fig1, width="stretch", key="fig1")
                if _fig.get("youth_share_pct") is not None:
                    st.caption(f"청년 비중 약 {_fig['youth_share_pct']}% · {_pop.get('insight') or ''}")
            else:
                st.info(
                    "청년 인구는 DB에서 읽었으나 시 전체 인구(읍면동 합계 표)가 없어 "
                    "비중 파이차트는 그리지 않습니다. 추정값으로 채우지 않습니다."
                )
                if _pop.get("data"):
                    st.write(_pop["data"])
        else:
            st.warning(
                "인구 요약을 DB에서 읽지 못했습니다. "
                f"{_pop.get('data') or _pop.get('error_detail') or ''}"
            )

    with col2:
        st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">🏠 2. 청년 주택 소유 비율 (%)</b></div>', unsafe_allow_html=True)
        if house_df is None or house_df.empty or "C2_NM" not in house_df.columns:
            st.warning("주택 표(gunsan_youth_housing_data)를 불러오지 못했습니다.")
            _h = get_gunsan_stat("housing")
            if _h.get("from_db"):
                st.caption(_h.get("source") or "")
                st.write(_h.get("data") or "")
        else:
            _h = get_gunsan_stat("housing")
            if _h.get("source"):
                st.caption(_h["source"])
            house_ratio = house_df[house_df["C2_NM"].str.contains("비율", na=False)].copy()
            house_ratio["DT"] = pd.to_numeric(house_ratio["DT"], errors="coerce")
            latest_year = house_ratio["PRD_DE"].max()
            latest_house = house_ratio[house_ratio["PRD_DE"] == latest_year]
            fig2 = px.bar(
                latest_house, x="C1_NM", y="DT",
                text="DT", title=f"{latest_year}년 연령대별 주택 소유 비율",
                labels={"C1_NM": "구분", "DT": "소유 비율(%)"},
                color="C1_NM", color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig2.update_traces(texttemplate="%{text}%", textposition="outside")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a")
            st.plotly_chart(fig2, width="stretch", key="fig2")

    st.write("---")
    
    # 📌 3 & 4번 영역
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">💰 3. 청년 소득 분포 (천 명)</b></div>', unsafe_allow_html=True)
        _inc = get_gunsan_stat("income")
        if _inc.get("source"):
            st.caption(_inc["source"])
        if wage_df is None or wage_df.empty or "DT" not in wage_df.columns:
            st.warning("임금 표(gunsan_youth_wage_data)를 불러오지 못했습니다.")
            if _inc.get("from_db"):
                st.write(_inc.get("data") or "")
        else:
            wage_plot = wage_df.copy()
            wage_plot["DT"] = pd.to_numeric(wage_plot["DT"], errors="coerce")
            latest_wage_year = wage_plot["PRD_DE"].max()
            latest_wage = wage_plot[wage_plot["PRD_DE"] == latest_wage_year]
            fig3 = px.bar(
                latest_wage, x="C2_NM", y="DT", color="C1_NM",
                title=f"{latest_wage_year}년 소득 구간별 인구",
                labels={"C2_NM": "소득 구간", "DT": "인구(천명)"},
                barmode="group",
            )
            fig3.update_layout(template="plotly_dark", paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a")
            st.plotly_chart(fig3, width="stretch", key="fig3")

    with col4:
        st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">🍺 4. 청년 건강 지표 (%)</b></div>', unsafe_allow_html=True)
        if health_df is None or health_df.empty or "DT" not in health_df.columns:
            st.warning("건강 표(gunsan_youth_health_data)를 불러오지 못했습니다.")
        else:
            health_plot = health_df.copy()
            health_plot["DT"] = pd.to_numeric(health_plot["DT"], errors="coerce")
            latest_health_year = health_plot["PRD_DE"].max()
            latest_health = health_plot[health_plot["PRD_DE"] == latest_health_year]
            fig4 = px.bar(
                latest_health, x="C2_NM", y="DT", color="C1_NM",
                title=f"{latest_health_year}년 생활 건강 지표 비교",
                labels={"C2_NM": "지표 구분", "DT": "비율(%)"},
                barmode="group", color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig4.update_layout(template="plotly_dark", paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a")
            st.plotly_chart(fig4, width="stretch", key="fig4")

    # 📌 5번 영역
    st.write("---")
    st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">📊 5. 군산시 청년(18~39세) 생활 지표 요약</b></div>', unsafe_allow_html=True)

    can_summary = (
        house_df is not None and not house_df.empty
        and health_df is not None and not health_df.empty
        and "C1_NM" in house_df.columns and "C1_NM" in health_df.columns
    )
    if not can_summary:
        st.warning("주택·건강 표가 부족해 요약 차트를 그리지 않습니다.")
    else:
        house_trend = house_df[
            (house_df["C1_NM"].str.contains("18~39세", na=False))
            & (house_df["C2_NM"].str.contains("비율", na=False))
        ].copy()
        health_trend = health_df[health_df["C1_NM"].str.contains("18~39세", na=False)].copy()
        house_trend["지표"] = "주택 소유 비율"
        health_trend["지표"] = health_trend["C2_NM"]
        combined_summary = pd.concat([
            house_trend[["DT", "지표"]],
            health_trend[["DT", "지표"]],
        ])
        combined_summary["DT"] = pd.to_numeric(combined_summary["DT"], errors="coerce")
        if combined_summary.empty or combined_summary["DT"].isna().all():
            st.warning("18~39세 요약 행을 찾지 못했습니다.")
        else:
            fig5 = px.bar(
                combined_summary, x="지표", y="DT", text="DT",
                title="군산시 청년 주요 지표 모아보기 (표 연도는 원본 PRD_DE 기준)",
                labels={"지표": "지표 종류", "DT": "수치(%)"},
                color="지표", color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig5.update_traces(texttemplate="%{text}%", textposition="outside")
            fig5.update_layout(template="plotly_dark", paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a")
            st.plotly_chart(fig5, width="stretch", key="fig5")

    # 📌 6번 영역 (취업의 어려움) — AI employment_difficulty 와 동일 표
    st.write("---")
    st.markdown('<div style="background:#1a1a1a; border-radius:12px; padding:12px; margin-bottom:8px; border:1px solid #333;"><b style="color:#f0f0f0;">🎯 6. 군산시 청년 취업의 어려움</b></div>', unsafe_allow_html=True)
    _emp = get_gunsan_stat("employment_difficulty")
    if _emp.get("source"):
        st.caption(_emp["source"])
    if _emp.get("metric"):
        _eu = _emp["metric"].get("unit_label_ko") or _emp["metric"].get("unit")
        st.caption(
            f"지표 정의: 지역={_emp['metric'].get('geography')} · "
            f"단위={_eu} · "
            f"(전북 취업자 수는 category=`employment_count`)"
        )

    if difficulty_df is None or difficulty_df.empty or "특성별2" not in difficulty_df.columns:
        st.warning("DB에서 '취업의 어려움 사회조사' 테이블을 불러오지 못했습니다.")
        if _emp.get("from_db") and _emp.get("data"):
            st.write(_emp["data"])
    else:
        st.markdown(
            '<div style="background:#222; color:#aaa; padding:8px; border-radius:8px; font-size:0.9em;">'
            "💡 공공데이터 포털 전북 사회조사 중 <b>군산시</b> 행만 사용 "
            "(AI <code>get_gunsan_youth_stats(employment_difficulty)</code> 와 동일 표)."
            "</div>",
            unsafe_allow_html=True,
        )
        gunsan_data = difficulty_df[difficulty_df["특성별2"] == "군산시"]
        if not gunsan_data.empty:
            exclude_cols = ["특성별1", "특성별2", "소계", "계"]
            valid_cols = [col for col in gunsan_data.columns if col not in exclude_cols]
            melted_gunsan = pd.melt(
                gunsan_data,
                id_vars=[],
                value_vars=valid_cols,
                var_name="어려움 요인",
                value_name="비율(%)",
            )
            melted_gunsan["비율(%)"] = pd.to_numeric(melted_gunsan["비율(%)"], errors="coerce")
            melted_gunsan = melted_gunsan.sort_values(by="비율(%)", ascending=False)
            fig6 = px.bar(
                melted_gunsan,
                x="비율(%)",
                y="어려움 요인",
                text="비율(%)",
                orientation="h",
                title="군산시 청년이 느끼는 취업의 어려움 요인 (단위: %)",
                color="비율(%)",
                color_continuous_scale="Blues",
            )
            fig6.update_traces(texttemplate="%{text}%", textposition="outside")
            fig6.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig6, width="stretch", key="fig6")
            with st.expander("🔍 군산시 원본 데이터 표 보기"):
                st.dataframe(gunsan_data[valid_cols], width="stretch")
        else:
            st.warning("데이터 내에서 '군산시' 행을 찾지 못했습니다.")
            st.dataframe(difficulty_df, width="stretch")

# 📌 7번 영역 (원룸 및 오피스텔 분포 - 정밀화 버전)
    st.write("---")
    st.subheader("🏠 7. 군산시 읍면동별 원룸 및 오피스텔 분포")
    
    if room_df is not None and not room_df.empty:
        st.info("💡 군산시의 청년들이 거주하기 좋은 원룸과 오피스텔이 어느 동네에 밀집해 있는지 보여주는 데이터입니다.")
        
        col_list = room_df.columns.tolist()
        dong_col = None
        for c in col_list:
            if '동' in c or '소재지' in c or '주소' in c:
                dong_col = c
                break
                
        if dong_col:
            # ✂️ [긴급 수술] 번지수가 붙은 상세주소에서 '동'까지만 싹둑 자릅니다.
            # 예: "전북특별자치도 군산시 소룡동 831" -> "소룡동"
            def extract_dong(address):
                if not address:
                    return "기타"
                # 공백으로 주소를 쪼갠 뒤, '동', '읍', '면'으로 끝나는 글자만 찾아냅니다.
                parts = str(address).split()
                for part in parts:
                    if part.endswith('동') or part.endswith('읍') or part.endswith('면'):
                        return part
                return "기타"
            
            # 새로운 '정제된_동네' 컬럼을 만들어 동만 쏙 뽑아 넣습니다.
            room_df['정제된_동네'] = room_df[dong_col].apply(extract_dong)
            
            # 묶어서 개수 세기!
            room_counts = room_df['정제된_동네'].value_counts().reset_index()
            room_counts.columns = ['동네', '건물 수']
            
            # '기타'로 빠진 데이터는 제외하고 상위 10개 추출
            room_counts = room_counts[room_counts['동네'] != '기타']
            top_rooms = room_counts.head(10)
            
            # 가로 막대 그래프 그리기
            fig7 = px.bar(
                top_rooms, x='건물 수', y='동네', text='건물 수',
                orientation='h', title="군산시 원룸 및 오피스텔 밀집 동네 Top 10",
                color='건물 수', color_continuous_scale='Purples'
            )
            fig7.update_traces(texttemplate='%{text}개', textposition='outside')
            fig7.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig7, width='stretch', key="fig7")
            
        else:
            st.warning("⚠️ 동네를 구분할 수 있는 컬럼을 찾지 못했습니다.")
            
        with st.expander("🔍 군산시 원룸 및 오피스텔 원본 표 보기"):
            st.dataframe(room_df, width='stretch')
    else:
        st.warning("⚠️ DB에서 '원룸 및 오피스텔 현황' 테이블을 불러오지 못했습니다.")

    # 📌 8. 전북 연령별 취업자 비중
    # 주의: 원표는 성별×분기 패널 → 단순 groupby SUM 은 중복 합산 버그.
    # AI·Main 과 동일: get_gunsan_stat("employment_count") 분기평균 수치 사용.
    st.write("---")
    st.subheader("💼 8. 전북특별자치도 연령별 취업자 비중")
    _ec = get_gunsan_stat("employment_count")
    if _ec.get("source"):
        st.caption(_ec["source"])
    if _ec.get("metric"):
        m = _ec["metric"]
        _u = m.get("unit_label_ko") or m.get("unit")
        st.caption(
            f"집계: {m.get('aggregation')} · 지역={m.get('geography')} · "
            f"연령={m.get('age_band')} · 단위={_u} "
            f"(AI category=`employment_count`)"
        )
        if m.get("unit_note"):
            st.caption(f"단위 주의: {m['unit_note']}")
    st.info(
        "💡 전북 **전체** 취업자 중 청년층(15~39세) 비중입니다. "
        "군산시 단독 수치가 아니며, 성별·분기를 한꺼번에 합치지 않고 **분기평균**을 씁니다. "
        "원표에 단위 컬럼이 없어 절대 규모는 **통상 천명**으로 읽되, 비중(%)은 단위와 무관합니다."
    )

    if _ec.get("from_db") and (_ec.get("figures") or {}).get("youth_15_39_quarterly_mean") is not None:
        try:
            _figc = _ec["figures"]
            youth_v = float(_figc["youth_15_39_quarterly_mean"])
            total_v = float(_figc.get("all_ages_quarterly_mean") or 0)
            other_v = max(0.0, total_v - youth_v)
            year_v = _figc.get("year") or "?"
            pie_job = pd.DataFrame(
                {
                    "연령_그룹": ["청년층 (15~39세)", "그 외 연령대"],
                    "취업자수": [youth_v, other_v],
                }
            )
            fig8 = px.pie(
                pie_job,
                values="취업자수",
                names="연령_그룹",
                title=f"{year_v}년 전북 취업자 중 청년층 비율 (분기평균)",
                color="연령_그룹",
                color_discrete_map={
                    "청년층 (15~39세)": "#3498DB",
                    "그 외 연령대": "#E5E7E9",
                },
            )
            fig8.update_traces(textinfo="percent+label", textfont_size=15, pull=[0.05, 0])
            st.plotly_chart(fig8, width="stretch", key="fig8")
            st.caption(_ec.get("data") or "")
            if _figc.get("by_age_quarterly_mean"):
                with st.expander("🔍 연령대별 분기평균 (남+여)"):
                    st.dataframe(
                        pd.DataFrame(_figc["by_age_quarterly_mean"]),
                        width="stretch",
                    )
            if job_df is not None and not job_df.empty:
                with st.expander("🔍 원본 표 (성별×분기 패널 — 합산 시 주의)"):
                    st.caption("이 원표를 그대로 SUM 하면 분기·성별이 중복됩니다. 차트는 분기평균만 사용합니다.")
                    st.dataframe(job_df, width="stretch")
        except Exception as e:
            st.error(f"취업자 비중 차트 오류: {e}")
            if _ec.get("data"):
                st.write(_ec["data"])
    else:
        st.warning(
            "employment_count 를 DB에서 읽지 못했습니다. "
            f"{_ec.get('data') or _ec.get('error_detail') or ''}"
        )

# 📌 9. 군산시 청년도약계좌 취급은행 현황 (최종 UI 개선 버전)
    st.write("---")
    st.subheader("💰 9. 청년도약계좌 취급은행 현황")
    
    if 'saving_df' in locals() and saving_df is not None and not saving_df.empty:
        st.info("💡 군산시 청년들이 도약계좌를 개설할 수 있는 취급 은행 목록입니다.")
        
        try:
            # 은행명 컬럼에서 고유한 은행 이름들만 쏙 뽑아내기
            bank_col = '은행명'
            banks = saving_df[bank_col].dropna().unique().tolist()
            
            st.markdown("#### 🏦 가입 가능한 제휴 은행 (가나다순)")
            
            # 은행 목록을 가나다순으로 정렬
            banks.sort()
            
            # 한 줄에 3개씩 예쁜 카드로 배치하기 위해 Streamlit 컬럼 기능 활용!
            for i in range(0, len(banks), 3):
                cols = st.columns(3)
                # 첫 번째 칸
                if i < len(banks):
                    cols[0].success(f"**{banks[i]}**")
                # 두 번째 칸
                if i+1 < len(banks):
                    cols[1].success(f"**{banks[i+1]}**")
                # 세 번째 칸
                if i+2 < len(banks):
                    cols[2].success(f"**{banks[i+2]}**")
            
            st.write("") # 줄바꿈용 공백
            
            # 원본 데이터도 하단에 얌전히 묻어두기
            with st.expander("🔍 원본 데이터 표 보기"):
                st.dataframe(saving_df, width='stretch')
                
        except Exception as e:
            st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {e}")
            st.dataframe(saving_df, width='stretch')
            
    else:
        st.warning("⚠️ DB에서 '청년도약계좌' 테이블을 불러오지 못했습니다.")
    
# --- DB 차트 블록 끝 (실패해도 st.stop 없음 · 푸터/피드백 유지) ---
except FileNotFoundError as e:
    st.error(
        f"🚨 DB/파일을 찾을 수 없습니다: {e}\n\n"
        f"경로: `{GUNSAN_STATS_DB_PATH}` · 시드 DB 또는 KOSIS 동기화 후 다시 열어보세요."
    )
except Exception as e:
    st.error(
        f"🚨 차트 로드 중 오류: {e}\n\n"
        "페이지는 유지됩니다. 위 유지보수에서 동기화·키 상태를 확인하세요."
    )



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# (removed duplicate github image footer - not needed for data page)



from finfit_youth.config import render_feedback_form
render_feedback_form(key_prefix="gunsan_stats")





