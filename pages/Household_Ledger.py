import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import textwrap

from finfit_youth.config import inject_finfit_theme, LEVELS

st.set_page_config(page_title="가계부", page_icon="📒", layout="wide")
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
  <div style="font-size: 1.6em; font-weight: 800; color: #f0f0f0;">📒 가계부</div>
  <div style="font-size: 0.95em; color: #888;">지출 기록 · 월별 분석 · 예산 관리</div>
</div>
"""
    ),
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════
# ★ 시트 ID (배포 시 secrets 와 함께 설정)
SHEET_ID = "1pEUv0K4Iva7yZTOk5Y6TAwWklU2w_4YN53ekdywPY_Q"
# ══════════════════════════════════════════════════

CATEGORIES = {
    "고정비": ["월세/관리비", "통신비", "보험료", "교통비", "구독서비스"],
    "식비": ["식료품", "외식", "카페·음료"],
    "여가": ["취미·문화", "여행", "친구 모임", "쇼핑"],
    "저축": ["적금", "비상금", "투자"],
    "기타": ["의료비", "교육·자기계발", "기타"],
}

# ── 세션 기본값 ───────────────────────────────────
if "income" not in st.session_state:
    st.session_state.income = 2000000
    st.session_state.income_touched = False
if "level" not in st.session_state:
    st.session_state.level = 5
if "LEVELS" not in st.session_state:
    st.session_state.LEVELS = LEVELS
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "ledger_backend" not in st.session_state:
    st.session_state.ledger_backend = None  # "sheets" | "session"
if "ledger_backend_detail" not in st.session_state:
    st.session_state.ledger_backend_detail = ""

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _secrets_have_gcp() -> bool:
    try:
        return "gcp_service_account" in st.secrets and bool(st.secrets["gcp_service_account"])
    except Exception:
        return False


def connect_sheet():
    """
    Try Google Sheets. Returns (worksheet|None, error_message|None).
    Never raises to the page body — callers decide session fallback.
    """
    if not _secrets_have_gcp():
        return None, "st.secrets 에 gcp_service_account 가 없습니다."
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=SCOPES,
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["날짜", "대분류", "소분류", "금액", "메모"])
        return sheet, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def load_from_sheets() -> tuple[list, str | None]:
    sheet, err = connect_sheet()
    if err or sheet is None:
        return [], err or "시트 연결 실패"
    try:
        records = sheet.get_all_records()
        # normalize keys
        out = []
        for r in records or []:
            if not isinstance(r, dict):
                continue
            row = {
                "날짜": str(r.get("날짜") or r.get("date") or ""),
                "대분류": str(r.get("대분류") or r.get("category") or ""),
                "소분류": str(r.get("소분류") or r.get("sub") or ""),
                "금액": int(float(str(r.get("금액") or r.get("amount") or 0).replace(",", "") or 0)),
                "메모": str(r.get("메모") or r.get("memo") or ""),
            }
            if row["대분류"] or row["금액"]:
                out.append(row)
        return out, None
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"


def save_row_to_sheets(row: dict) -> str | None:
    """Return error string or None on success."""
    sheet, err = connect_sheet()
    if err or sheet is None:
        return err or "시트 연결 실패"
    try:
        sheet.append_row(
            [
                row["날짜"],
                row["대분류"],
                row["소분류"],
                row["금액"],
                row.get("메모") or "",
            ]
        )
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def delete_all_sheets() -> str | None:
    sheet, err = connect_sheet()
    if err or sheet is None:
        return err or "시트 연결 실패"
    try:
        sheet.clear()
        sheet.append_row(["날짜", "대분류", "소분류", "금액", "메모"])
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def ensure_backend():
    """Pick sheets if possible, else session. Sets session_state flags."""
    if st.session_state.ledger_backend in ("sheets", "session"):
        return st.session_state.ledger_backend

    records, err = load_from_sheets()
    if err is None:
        st.session_state.ledger_backend = "sheets"
        st.session_state.ledger_backend_detail = "Google Sheets 연동"
        # first connect: merge sheet into empty session list
        if not st.session_state.expenses:
            st.session_state.expenses = records
        return "sheets"

    st.session_state.ledger_backend = "session"
    st.session_state.ledger_backend_detail = err or "시트 미사용"
    return "session"


backend = ensure_backend()

# Status banner — honest about remote vs session
if backend == "sheets":
    st.success(
        "☁️ **저장소: Google Sheets** — 추가·초기화가 시트에도 반영됩니다. "
        f"[원본 시트 열기](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)"
    )
else:
    st.warning(
        "💾 **저장소: 브라우저 세션 (임시)** — Google Sheets에 연결하지 못했습니다. "
        "이 모드에서도 가계부 UI·차트·AI 연동(session `expenses`/`income`)은 동작합니다. "
        "배포·팀 공유 시 `.streamlit/secrets.toml` 에 `gcp_service_account` 를 설정하세요.\n\n"
        f"원인: `{st.session_state.ledger_backend_detail}`"
    )
    with st.expander("시트 연동 방법"):
        st.markdown(
            """
1. GCP 서비스 계정 JSON을 만들고 시트에 편집 권한 공유  
2. `.streamlit/secrets.toml` 예시:
```toml
[gcp_service_account]
type = "service_account"
# ... 나머지 필드
```
3. Streamlit 재시작 후 이 페이지를 다시 엽니다.
"""
        )

# Summary from real session data (not hardcoded demo figures)
_expenses = st.session_state.expenses or []
_income = int(st.session_state.income or 0)
_df_prev = pd.DataFrame(_expenses) if _expenses else pd.DataFrame(
    columns=["날짜", "대분류", "소분류", "금액", "메모"]
)
if not _df_prev.empty and "금액" in _df_prev.columns:
    _df_prev["금액"] = pd.to_numeric(_df_prev["금액"], errors="coerce").fillna(0).astype(int)
    _spend = int(_df_prev[_df_prev["대분류"] != "저축"]["금액"].sum()) if "대분류" in _df_prev.columns else int(_df_prev["금액"].sum())
    _saved = int(_df_prev[_df_prev["대분류"] == "저축"]["금액"].sum()) if "대분류" in _df_prev.columns else 0
else:
    _spend, _saved = 0, 0
_remain = _income - _spend - _saved

st.markdown("### 이번 달 요약")
sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
with sum_col1:
    st.metric("월 소득", f"{_income:,}원")
with sum_col2:
    st.metric("총 지출", f"{_spend:,}원")
with sum_col3:
    st.metric("저축", f"{_saved:,}원")
with sum_col4:
    st.metric("잔액", f"{_remain:,}원")

st.divider()

# ══════════════════════════════════════════════════
# 지출 입력 UI
# ══════════════════════════════════════════════════
with st.expander("➕ 지출 추가", expanded=True):
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        exp_date = st.date_input("날짜", value=date.today())
    with c2:
        cat_main = st.selectbox("대분류", list(CATEGORIES.keys()))
    with c3:
        cat_sub = st.selectbox("소분류", CATEGORIES[cat_main])
    with c4:
        amount = st.number_input("금액 (원)", min_value=0, step=1000, format="%d")
    with c5:
        memo = st.text_input("메모")

    if st.button("추가", use_container_width=True, type="primary"):
        if amount > 0:
            new_row = {
                "날짜": str(exp_date),
                "대분류": cat_main,
                "소분류": cat_sub,
                "금액": int(amount),
                "메모": memo,
            }
            # Always keep session (AI sync + UI)
            st.session_state.expenses.append(new_row)
            if backend == "sheets":
                serr = save_row_to_sheets(new_row)
                if serr:
                    st.warning(
                        f"세션에는 저장됐지만 **시트 동기화 실패**: {serr}. "
                        "세션 모드로 전환합니다."
                    )
                    st.session_state.ledger_backend = "session"
                    st.session_state.ledger_backend_detail = serr
                else:
                    st.success("✅ 저장됐어요! (Google Sheets + 세션)")
            else:
                st.success("✅ 세션에 저장됐어요! (시트 미연결 — 브라우저 세션에만 유지)")
            st.rerun()
        else:
            st.warning("금액을 입력해주세요!")

# ── 데이터 없을 때: stop 하지 않고 안내만 ────────────────
if not st.session_state.expenses:
    st.info("아직 지출 내역이 없어요. 위에서 추가해보세요! (차트가 아래에 채워집니다.)")
else:
    # ══════════════════════════════════════════════════
    # 데이터 분석 및 시각화
    # ══════════════════════════════════════════════════
    df = pd.DataFrame(st.session_state.expenses)
    df["금액"] = pd.to_numeric(df["금액"], errors="coerce").fillna(0).astype(int)

    income = int(st.session_state.income)
    total = int(df[df["대분류"] != "저축"]["금액"].sum())
    saved = int(df[df["대분류"] == "저축"]["금액"].sum())
    remain = income - total - saved

    st.divider()
    cols = st.columns(4)
    cols[0].metric("월 소득", f"{income:,}원")
    cols[1].metric("총 지출", f"{total:,}원", delta=f"-{total:,}원", delta_color="inverse")
    cols[2].metric("저축", f"{saved:,}원", delta=f"+{saved:,}원")
    cols[3].metric("남은 금액", f"{remain:,}원", delta_color="normal")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("카테고리별 지출")
        spend_df = df[df["대분류"] != "저축"]
        if spend_df.empty:
            st.caption("지출(비저축) 데이터가 없습니다.")
        else:
            summary = spend_df.groupby("대분류")["금액"].sum().reset_index()
            fig = px.pie(
                summary,
                values="금액",
                names="대분류",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.4,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("목표 대비 달성 현황")
        lv = st.session_state.get("LEVELS", LEVELS).get(
            st.session_state.level, {"save": 0.25, "fix": 0.55, "leisure": 0.20}
        )
        targets = {
            "저축": int(income * lv["save"]),
            "고정비": int(income * lv["fix"]),
            "여가·식비": int(income * lv["leisure"]),
        }
        actuals = {
            "저축": saved,
            "고정비": int(df[df["대분류"] == "고정비"]["금액"].sum()),
            "여가·식비": int(df[df["대분류"].isin(["여가", "식비"])]["금액"].sum()),
        }
        bar_df = pd.DataFrame(
            {
                "항목": list(targets.keys()),
                "목표": list(targets.values()),
                "실제": [actuals[k] for k in targets],
            }
        )
        fig2 = go.Figure()
        fig2.add_bar(name="목표", x=bar_df["항목"], y=bar_df["목표"], marker_color="#CBD5E8")
        fig2.add_bar(name="실제", x=bar_df["항목"], y=bar_df["실제"], marker_color="#F4A261")
        fig2.update_layout(barmode="group", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 전체 지출 내역")
    st.dataframe(
        df.sort_values("날짜", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
if st.button("🗑️ 전체 초기화", type="secondary"):
    if backend == "sheets":
        derr = delete_all_sheets()
        if derr:
            st.error(f"시트 초기화 실패: {derr}")
        else:
            st.session_state.expenses = []
            st.success("시트·세션 초기화 완료")
            st.rerun()
    else:
        st.session_state.expenses = []
        st.success("세션 지출 내역을 비웠습니다.")
        st.rerun()
