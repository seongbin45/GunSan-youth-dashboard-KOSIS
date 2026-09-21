import streamlit as st
import textwrap

from finfit_youth.config import inject_finfit_theme, secret_status
from finfit_youth.service import YouthDataService
from finfit_youth.trust_copy import policy_cache_meta

st.set_page_config(page_title="청년 혜택", page_icon="🎁", layout="wide")
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
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">🎁 온통청년 실시간 정책/청년센터/콘텐츠</div>
      <div style="font-size:12px;color:#888;">목록/검색은 캐시 데이터, 상세는 실시간 조회(단기 캐시). 키·네트워크 실패 시에도 페이지는 유지됩니다.</div>
    </div>
  </div>
</div>
"""
    ),
    unsafe_allow_html=True,
)

# ── API key status (not local-only: keys may come from secrets/env/hosting) ──
KEY_SPECS = [
    ("YOUTH_API_KEY", "정책(policy)"),
    ("YOUTH_CENTER_API_KEY", "청년센터(center)"),
    ("YOUTH_CONTENT_API_KEY", "콘텐츠(content)"),
]
key_rows = []
any_key = False
for name, label in KEY_SPECS:
    stt = secret_status(name)
    configured = bool(stt.get("configured"))
    src = stt.get("source") or "missing"
    if configured:
        any_key = True
    key_rows.append((name, label, configured, src, stt.get("masked") or ""))

if any_key:
    st.success(
        "온통청년 API 키 중 일부가 설정되어 있습니다. "
        "동기화·상세 조회는 해당 소스 키 권한에 따릅니다."
    )
else:
    st.warning(
        "⚠️ **온통청년 API 키가 없습니다.** 페이지는 열리며 **로컬 캐시(youth_cache.db)** 목록은 조회할 수 있습니다. "
        "신규 동기화·상세 실시간 조회는 키가 필요합니다. "
        "배포 환경이든 로컬이든 `.streamlit/secrets.toml` 또는 환경변수에 키를 넣으세요."
    )

with st.expander("API 키 상태 · 설정 안내", expanded=not any_key):
    for name, label, configured, src, masked in key_rows:
        if configured:
            st.write(f"- **{label}** (`{name}`): 설정됨 · 출처 `{src}` · `{masked}`")
        else:
            st.write(f"- **{label}** (`{name}`): **미설정**")
    st.markdown(
        """
```toml
# .streamlit/secrets.toml 예시
YOUTH_API_KEY = "정책용키"
YOUTH_CENTER_API_KEY = "센터용키"   # 선택
YOUTH_CONTENT_API_KEY = "콘텐츠용키"  # 선택
```
설정 후 Streamlit을 재시작하세요.  
캐시 DB: 프로젝트 루트 `youth_cache.db` (AI 혜택 매칭과 동일).
"""
    )

# Policy cache meta (always useful)
try:
    meta = policy_cache_meta()
    st.caption(
        f"정책 캐시: **{int(meta.get('cache_size') or 0):,}건** · "
        f"갱신 {meta.get('cache_age_text') or '불명'} · "
        f"`{meta.get('cache_db') or 'youth_cache.db'}`"
    )
except Exception:
    st.caption("정책 캐시 메타를 읽지 못했습니다.")

service = YouthDataService()

# Background scheduler only if at least policy key looks configured —
# still never crash the page if start fails.
if "youth_scheduler" not in st.session_state:
    try:
        if any_key:
            from finfit_youth.scheduler import ensure_scheduler_started

            st.session_state.youth_scheduler = ensure_scheduler_started(
                service, interval_seconds=30 * 60
            )
            st.session_state.youth_scheduler_note = "30분 주기 백그라운드 동기화 시작됨"
        else:
            st.session_state.youth_scheduler = None
            st.session_state.youth_scheduler_note = "API 키 없음 — 백그라운드 동기화 미시작"
    except Exception as e:
        st.session_state.youth_scheduler = None
        st.session_state.youth_scheduler_note = f"스케줄러 시작 실패: {e}"

if st.session_state.get("youth_scheduler_note"):
    st.caption(st.session_state["youth_scheduler_note"])

left, right = st.columns([2, 1])

with left:
    source_label = st.selectbox("데이터 구분", ["정책", "청년센터", "콘텐츠"], index=0)
    source_map = {"정책": "policy", "청년센터": "center", "콘텐츠": "content"}
    source = source_map[source_label]

    query = st.text_input("검색어", placeholder="예: 취업, 주거, 금융")

    size_label = st.selectbox("한 화면에 표시할 목록 개수", [10, 20, 30, 50, 100, "Max"], index=2)
    size = 9999 if size_label == "Max" else int(size_label)

    if size_label == "Max":
        page = 1
        st.caption("Max 선택 시 페이지는 1개로 고정됩니다.")
    else:
        page = st.number_input("페이지 번호", min_value=1, value=1, step=1)

    refresh_clicked = st.button("지금 동기화", type="primary")
    if refresh_clicked:
        with st.spinner("동기화 중..."):
            try:
                result = service.sync_source(source)
                st.success(f"{source_label} 동기화 완료: {result['count']}건")
            except Exception as e:
                msg = str(e)
                if "not set" in msg.lower() or "api_key" in msg.lower() or "API_KEY" in msg:
                    st.error(
                        f"동기화 실패: API 키가 없거나 비어 있습니다. ({e})\n\n"
                        "secrets/환경변수 설정 후 재시작하세요. "
                        "기존 캐시가 있으면 아래 목록은 계속 볼 수 있습니다."
                    )
                elif source == "content" and ("403" in msg or "400" in msg):
                    st.error(
                        "동기화 실패: 콘텐츠 API 키 권한 또는 파라미터"
                        "(apiKeyNm/pageType/pstSn/rtnType)를 확인해주세요."
                    )
                elif source == "center" and ("403" in msg or "400" in msg):
                    st.error(
                        "동기화 실패: 청년센터 API 키 권한 또는 파라미터"
                        "(apiKeyNm/pageType/plcSn/rtnType)를 확인해주세요."
                    )
                else:
                    st.error(f"동기화 실패: {e}")
                # no st.stop() — keep page usable for cache browse

with right:
    st.info(
        "운영 안내\n\n"
        "- 정책/청년센터/콘텐츠 API 키를 각각 설정 "
        "(`YOUTH_API_KEY`, `YOUTH_CENTER_API_KEY`, `YOUTH_CONTENT_API_KEY`)\n"
        "- 키 있으면 30분 주기 자동 동기화 시도\n"
        "- 외부 API 오류 시 **직전 스냅샷 캐시 폴백**\n"
        "- AI 혜택 매칭은 이 캐시(`snapshot:policy`)를 사용"
    )

# ── List from cache (never stop the page) ──
result = {"items": [], "total": 0, "page": int(page), "size": int(size)}
try:
    result = service.get_list(
        source=source, query=query, page=int(page), size=int(size)
    )
except Exception as e:
    st.error(
        f"목록 조회 실패: {e}\n\n"
        "캐시가 비었거나 DB 경로 문제일 수 있습니다. "
        "키를 설정한 뒤 **지금 동기화**를 실행하세요."
    )

st.divider()
st.write(f"총 {result.get('total', 0)}건")

items = result.get("items") or []
if not items:
    st.warning(
        "표시할 데이터가 없습니다. "
        "1) API 키 설정 후 동기화, 2) `youth_cache.db` 존재 여부, "
        "3) 검색어 완화 를 확인하세요. "
        "페이지는 계속 사용할 수 있습니다."
    )

for idx, item in enumerate(items):
    title = item.get("title") or "제목 없음"
    summary = item.get("summary") or "요약 정보 없음"
    region = item.get("region") or "지역 정보 없음"
    item_id = item.get("id") or ""
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}

    with st.expander(f"{title} ({region})"):
        st.write(summary)

        if source == "center":
            tel = raw.get("cntrTelno") or "전화번호 정보 없음"
            addr = " ".join(
                x
                for x in [
                    str(raw.get("cntrAddr") or "").strip(),
                    str(raw.get("cntrDaddr") or "").strip(),
                ]
                if x
            ) or "주소 정보 없음"
            url = raw.get("cntrUrlAddr")

            st.caption(f"전화: {tel}")
            st.caption(f"주소: {addr}")
            if url:
                st.markdown(f"센터 URL: [{url}]({url})")

        if item_id:
            if st.button("상세 실시간 조회", key=f"detail-{source}-{item_id}-{idx}"):
                try:
                    detail = service.get_detail(source=source, item_id=item_id)
                    st.json(detail)
                except Exception as e:
                    msg = str(e)
                    if "not set" in msg.lower() or "API_KEY" in msg:
                        st.error(f"상세 조회 실패: API 키 필요 — {e}")
                    elif source == "content" and ("403" in msg or "400" in msg):
                        st.error(
                            "상세 조회 실패: 콘텐츠 API 권한 또는 상세 파라미터"
                            "(pstSn/pageType/rtnType)를 확인해주세요."
                        )
                    elif source == "center" and ("403" in msg or "400" in msg):
                        st.error(
                            "상세 조회 실패: 청년센터 API 권한 또는 상세 파라미터"
                            "(plcSn/pageType/rtnType)를 확인해주세요."
                        )
                    else:
                        st.error(f"상세 조회 실패: {e}")
        else:
            st.caption("상세 조회를 위한 식별자가 없어 목록 데이터만 표시합니다.")
