import os

try:
    import streamlit as st
except Exception:
    st = None


def _secret(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v:
        return v
    if st is not None:
        try:
            return str(st.secrets.get(name, default))
        except Exception:
            pass
    return default

def _safe_base_url(v: str) -> str:
    v = (v or "").strip()
    if (not v) or (":8080" in v) or (not v.startswith("https://")):
        return "https://www.youthcenter.go.kr"
    return v.rstrip("/")

def _safe_path(v: str, default: str) -> str:
    v = (v or "").strip()
    if not v:
        return default
    if not v.startswith("/"):
        v = "/" + v
    return v



YOUTH_API_BASE_URL = _safe_base_url(
    _secret("YOUTH_API_BASE_URL", "https://www.youthcenter.go.kr")
)
YOUTH_API_KEY = _secret("YOUTH_API_KEY", "")

YOUTH_POLICY_LIST_PATH = _safe_path(
    _secret("YOUTH_POLICY_LIST_PATH", "/opi/youthPlcyList.do"),
    "/opi/youthPlcyList.do",
)
YOUTH_SPACE_LIST_PATH = _safe_path(
    _secret("YOUTH_SPACE_LIST_PATH", "/opi/youthSpaceList.do"),
    "/opi/youthSpaceList.do",
)
YOUTH_CONTENT_LIST_PATH = _safe_path(
    _secret("YOUTH_CONTENT_LIST_PATH", "/opi/youthContentList.do"),
    "/opi/youthContentList.do",
)

YOUTH_POLICY_DETAIL_PATH = _safe_path(
    _secret("YOUTH_POLICY_DETAIL_PATH", "/opi/youthPlcyDtl.do"),
    "/opi/youthPlcyDtl.do",
)
YOUTH_SPACE_DETAIL_PATH = _safe_path(
    _secret("YOUTH_SPACE_DETAIL_PATH", "/opi/youthSpaceDtl.do"),
    "/opi/youthSpaceDtl.do",
)
YOUTH_CONTENT_DETAIL_PATH = _safe_path(
    _secret("YOUTH_CONTENT_DETAIL_PATH", "/opi/youthContentDtl.do"),
    "/opi/youthContentDtl.do",
)
YOUTH_API_BASE_URL = _safe_base_url(
    _secret("YOUTH_API_BASE_URL", "https://www.youthcenter.go.kr")
)
YOUTH_API_KEY = _secret("YOUTH_API_KEY", "")

YOUTH_POLICY_LIST_PATH = _safe_path(
    _secret("YOUTH_POLICY_LIST_PATH", "/opi/youthPlcyList.do"),
    "/opi/youthPlcyList.do",
)
YOUTH_SPACE_LIST_PATH = _safe_path(
    _secret("YOUTH_SPACE_LIST_PATH", "/opi/youthSpaceList.do"),
    "/opi/youthSpaceList.do",
)
YOUTH_CONTENT_LIST_PATH = _safe_path(
    _secret("YOUTH_CONTENT_LIST_PATH", "/opi/youthContentList.do"),
    "/opi/youthContentList.do",
)

YOUTH_POLICY_DETAIL_PATH = _safe_path(
    _secret("YOUTH_POLICY_DETAIL_PATH", "/opi/youthPlcyDtl.do"),
    "/opi/youthPlcyDtl.do",
)
YOUTH_SPACE_DETAIL_PATH = _safe_path(
    _secret("YOUTH_SPACE_DETAIL_PATH", "/opi/youthSpaceDtl.do"),
    "/opi/youthSpaceDtl.do",
)
YOUTH_CONTENT_DETAIL_PATH = _safe_path(
    _secret("YOUTH_CONTENT_DETAIL_PATH", "/opi/youthContentDtl.do"),
    "/opi/youthContentDtl.do",
)


