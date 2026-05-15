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



YOUTH_API_BASE_URL = _secret("YOUTH_API_BASE_URL", "https://www.youthcenter.go.kr")

YOUTH_POLICY_LIST_PATH = _secret("YOUTH_POLICY_LIST_PATH", "/opi/youthPlcyList.do")
YOUTH_SPACE_LIST_PATH = _secret("YOUTH_SPACE_LIST_PATH", "/opi/youthSpaceList.do")
YOUTH_CONTENT_LIST_PATH = _secret("YOUTH_CONTENT_LIST_PATH", "/opi/youthContentList.do")

YOUTH_POLICY_DETAIL_PATH = _secret("YOUTH_POLICY_DETAIL_PATH", "/opi/youthPlcyDtl.do")
YOUTH_SPACE_DETAIL_PATH = _secret("YOUTH_SPACE_DETAIL_PATH", "/opi/youthSpaceDtl.do")
YOUTH_CONTENT_DETAIL_PATH = _secret("YOUTH_CONTENT_DETAIL_PATH", "/opi/youthContentDtl.do")

CACHE_DB_PATH = _secret("YOUTH_CACHE_DB_PATH", "youth_cache.db")
CACHE_TTL_SECONDS = int(_secret("YOUTH_CACHE_TTL_SECONDS", "1800"))
DETAIL_TTL_SECONDS = int(_secret("YOUTH_DETAIL_TTL_SECONDS", "120"))

HTTP_TIMEOUT_SECONDS = float(_secret("YOUTH_API_TIMEOUT_SECONDS", "8"))
HTTP_MAX_RETRIES = int(_secret("YOUTH_API_MAX_RETRIES", "3"))
HTTP_BACKOFF_SECONDS = float(_secret("YOUTH_API_BACKOFF_SECONDS", "0.7"))
HTTP_RATE_LIMIT_PER_MINUTE = int(_secret("YOUTH_API_RATE_LIMIT_PER_MINUTE", "120"))

