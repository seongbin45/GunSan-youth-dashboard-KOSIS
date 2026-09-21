"""Dedicated not-found page (deep link / switch_page fallback)."""
import streamlit as st

from finfit_youth.page_router import render_not_found

st.set_page_config(
    page_title="페이지를 찾을 수 없음 · FinFit",
    page_icon="🧭",
    layout="wide",
)

# Optional: prior router stored what the user asked for
_requested = st.session_state.pop("_not_found_requested", None)
_reason = st.session_state.pop("_not_found_reason", None)

render_not_found(requested=_requested, reason=_reason)
