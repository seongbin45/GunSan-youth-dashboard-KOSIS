"""
Soft page routing + FinFit-branded not-found UI.

Streamlit multipage has no official custom HTTP 404 for arbitrary paths.
This module covers:
  - `?page=<slug>` query navigators (app.py / 0_Home)
  - failed `st.switch_page` → branded fallback
  - dedicated `pages/99_…` entry for direct open / deep links
"""
from __future__ import annotations

import textwrap
from typing import Any, Mapping, Optional

# Query slug → pages/ path (stable deep-link contract)
PAGE_ROUTES: dict[str, str] = {
    "home": "pages/0_Home.py",
    "ai": "pages/2_AI와_대화하기.py",
    "benefit": "pages/4_군산시민 맞춤 혜택 찾기.py",
    "benefits": "pages/4_군산시민 맞춤 혜택 찾기.py",
    "Government_Backed_Benefits": "pages/3_정부 지원 혜택 목록.py",
    "gov_benefits": "pages/3_정부 지원 혜택 목록.py",
    "finance": "pages/5_금융용어.py",
    "terms": "pages/5_금융용어.py",
    "stats": "pages/6_군산시 청년 데이터.py",
    "gunsan": "pages/6_군산시 청년 데이터.py",
    "youth": "pages/7_청년혜택업데이트.py",
    "youth_update": "pages/7_청년혜택업데이트.py",
    "Household_Ledger": "pages/Household_Ledger.py",
    "ledger": "pages/Household_Ledger.py",
    "Savings_Step_Setting_Guide": "pages/Savings_Step_Setting_Guide.py",
    "savings": "pages/Savings_Step_Setting_Guide.py",
    "main": "pages/Main_Screen.py",
    "onboarding": "pages/Onboarding.py",
    "404": "pages/99_페이지를_찾을_수_없음.py",
    "not_found": "pages/99_페이지를_찾을_수_없음.py",
}

# Aliases normalized to lower for lookup of mixed-case slugs
_LOWER_ALIASES = {k.lower(): v for k, v in PAGE_ROUTES.items()}

NOT_FOUND_PAGE = "pages/99_페이지를_찾을_수_없음.py"

# Safe landing targets shown on the 404 screen
HOME_LINKS: list[tuple[str, str, str]] = [
    ("홈", "pages/0_Home.py", "메인으로"),
    ("AI 대화", "pages/2_AI와_대화하기.py", "금융 AI"),
    ("맞춤 혜택", "pages/4_군산시민 맞춤 혜택 찾기.py", "혜택 매칭"),
    ("가계부", "pages/Household_Ledger.py", "수입·지출"),
    ("군산 데이터", "pages/6_군산시 청년 데이터.py", "KOSIS 통계"),
]


def resolve_page_path(slug: str | None) -> Optional[str]:
    if slug is None:
        return None
    raw = str(slug).strip()
    if not raw:
        return None
    if raw in PAGE_ROUTES:
        return PAGE_ROUTES[raw]
    return _LOWER_ALIASES.get(raw.lower())


def safe_switch_page(path: str) -> bool:
    """st.switch_page without crashing the app. Returns True if navigated."""
    import streamlit as st

    try:
        st.switch_page(path)
        return True
    except Exception:
        return False


def render_not_found(
    *,
    requested: str | None = None,
    reason: str | None = None,
    show_links: bool = True,
) -> None:
    """FinFit-themed 404 body (no st.set_page_config — caller owns that)."""
    import streamlit as st

    try:
        from .config import inject_finfit_theme

        inject_finfit_theme()
    except Exception:
        pass

    st.markdown(
        """
<style>
.stApp { background: #111111 !important; }
</style>
""",
        unsafe_allow_html=True,
    )

    req = (requested or "").strip()
    why = (reason or "").strip()

    st.markdown(
        textwrap.dedent(
            f"""
<div style="background:#1a1a1a; padding:28px 20px; margin:12px 0 16px; border:1px solid #333;
            border-radius:16px; text-align:center;">
  <div style="font-size:48px; line-height:1; margin-bottom:8px;">🧭</div>
  <div style="font-size:42px; font-weight:800; color:#f0f0f0; letter-spacing:2px;">404</div>
  <div style="font-size:18px; font-weight:700; color:#f0f0f0; margin-top:8px;">
    페이지를 찾을 수 없습니다
  </div>
  <div style="font-size:13px; color:#888; margin-top:10px; line-height:1.55;">
    주소가 바뀌었거나, 잘못된 링크·쿼리일 수 있습니다.<br/>
    FinFit 홈에서 다시 이동해 주세요. (앱은 정상 동작 중이며 데이터는 유지됩니다)
  </div>
  {"<div style='margin-top:12px;font-size:12px;color:#A5B4FC;'>요청: <code style='color:#c4b5fd;'>" + _esc(req) + "</code></div>" if req else ""}
  {"<div style='margin-top:6px;font-size:12px;color:#888;'>" + _esc(why) + "</div>" if why else ""}
</div>
"""
        ),
        unsafe_allow_html=True,
    )

    st.info(
        "💡 **팁:** `?page=ai` 처럼 알려진 슬러그만 라우팅됩니다. "
        "예: `ai`, `benefit`, `ledger`, `stats`, `youth`, `home`."
    )

    if show_links:
        st.markdown("#### 바로 가기")
        cols = st.columns(min(3, len(HOME_LINKS)))
        for i, (label, path, hint) in enumerate(HOME_LINKS):
            with cols[i % len(cols)]:
                try:
                    st.page_link(path, label=f"→ {label}", help=hint)
                except Exception:
                    if st.button(label, key=f"nf_btn_{i}", use_container_width=True):
                        safe_switch_page(path)

        if st.button("🏠 홈으로", type="primary", use_container_width=True, key="nf_home_primary"):
            if not safe_switch_page("pages/0_Home.py"):
                safe_switch_page("app.py")

    with st.expander("알려진 page 슬러그", expanded=False):
        rows = sorted({(k, v) for k, v in PAGE_ROUTES.items() if k not in ("404", "not_found")})
        for slug, path in rows:
            st.write(f"- `{slug}` → `{path}`")


def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def handle_query_page_param(
    query_params: Optional[Mapping[str, Any]] = None,
) -> bool:
    """
    If `page` query param is set: route to page or render 404.

    Returns True when the caller should stop rendering the current page body
    (navigated away, or 404 UI already drawn).
    """
    import streamlit as st

    qp = query_params if query_params is not None else st.query_params
    if "page" not in qp:
        return False

    try:
        target = qp.get("page")
    except Exception:
        target = None
    # query_params may return list-like
    if isinstance(target, (list, tuple)):
        target = target[0] if target else ""
    target_s = str(target or "").strip()

    try:
        st.query_params.clear()
    except Exception:
        pass

    if not target_s:
        return False

    path = resolve_page_path(target_s)
    if path:
        if safe_switch_page(path):
            return True
        # known slug but file missing / switch failed
        render_not_found(
            requested=target_s,
            reason=f"등록된 경로로 이동하지 못했습니다: `{path}`",
        )
        return True

    render_not_found(
        requested=target_s,
        reason="알 수 없는 page 슬러그입니다.",
    )
    return True
