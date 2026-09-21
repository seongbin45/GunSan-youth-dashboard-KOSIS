"""
Fixed provenance / disclaimer copy for benefits + stats.

Single source of truth so pages and AI tools never invent softer wording.
Not a legal document — product honesty for prototype UX.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

# --- Benefits (온통청년 cache matcher) ---

BENEFITS_METHOD = (
    "휴리스틱 점수 매칭(지역·연령·고용·주택·키워드 텍스트). "
    "행정·공고의 공식 자격 심사 결과가 아닙니다."
)

BENEFITS_DISCLAIMER = (
    "본 결과는 **신청 가능 확정이 아닙니다.** "
    "소득·거소·중복 수혜·모집 기간 등은 공식 공고·신청 페이지에서 반드시 확인하세요. "
    "정책은 수시로 변경될 수 있습니다."
)

BENEFITS_LIMITATIONS = [
    "캐시 스냅샷 기준 시점의 목록만 반영 (실시간 전체 공고 아님)",
    "연령 hard filter 외 소득·세부 자격은 점수 가중에 가깝고 탈락 확정이 아님",
    "캐시가 비거나 매칭이 없으면 소량 로컬 폴백 목록 사용 — 실데이터가 아님",
    "군산·전북 가점은 텍스트/zip 휴리스틱",
]

# --- Stats (KOSIS / local gunsan_youth_data.db) ---

STATS_METHOD = (
    "로컬 SQLite(gunsan_youth_data.db) 조회. "
    "페이지 차트와 AI 통계 툴이 동일 모듈(finfit_youth.gunsan_stats)을 사용."
)

STATS_DISCLAIMER = (
    "수치는 **DB에 있는 값만** 표시합니다. 없는 값은 추정으로 채우지 않습니다. "
    "표마다 조사·공표 연도가 다르며 KOSIS/공공데이터 원문의 시차가 있을 수 있습니다. "
    "해석·인용 시 출처 표기(표명·연도)를 확인하세요."
)

STATS_LIMITATIONS = [
    "핵심 KOSIS 표는 동기화 시점 스냅샷",
    "employment_difficulty=군산 사회조사 응답% / employment_count=전북 취업자 규모(분기평균) — 단위·지역 상이",
    "청년 연령 정의가 표마다 다를 수 있음 (인구 18~39 vs 취업자 15~39)",
    "연령별취업자는 성별·분기로 쪼개져 있어 단순 SUM 금지(분기평균 사용)",
]


def format_age_seconds(seconds: Optional[int]) -> str:
    if seconds is None:
        return "동기화 시각 없음(미기록 또는 미동기화)"
    try:
        s = int(seconds)
    except Exception:
        return "동기화 시각 불명"
    if s < 0:
        return "동기화 시각 불명"
    if s < 60:
        return f"약 {s}초 전"
    if s < 3600:
        return f"약 {s // 60}분 전"
    if s < 86400:
        return f"약 {s // 3600}시간 전"
    return f"약 {s // 86400}일 전"


def policy_cache_meta(store=None) -> dict[str, Any]:
    """OnTong youth policy snapshot size + age."""
    from .cache_store import CacheStore
    from .config import CACHE_DB_PATH

    store = store or CacheStore(CACHE_DB_PATH)
    snap = store.get("snapshot:policy", max_age_seconds=None)
    size = len(snap) if isinstance(snap, list) else 0
    age = store.age_seconds("snapshot:policy")
    return {
        "cache_key": "snapshot:policy",
        "cache_size": size,
        "cache_age_seconds": age,
        "cache_age_text": format_age_seconds(age),
        "cache_db": str(CACHE_DB_PATH),
        "empty": size == 0,
    }


def enrich_benefits_result(result: dict[str, Any], store=None) -> dict[str, Any]:
    """Attach fixed trust fields to match_benefits / match_benefits_for_ui output."""
    out = dict(result or {})
    meta = policy_cache_meta(store)
    data_source = str(out.get("data_source") or "")
    is_fallback = "폴백" in data_source or data_source.startswith("로컬")
    out.setdefault("cache_size", meta["cache_size"])
    out["cache_age_seconds"] = meta["cache_age_seconds"]
    out["cache_age_text"] = meta["cache_age_text"]
    out["cache_db"] = meta["cache_db"]
    out["is_fallback"] = is_fallback
    out["method"] = BENEFITS_METHOD
    out["disclaimer"] = BENEFITS_DISCLAIMER
    out["limitations"] = list(BENEFITS_LIMITATIONS)
    return out


def benefits_trust_lines(meta: Optional[dict[str, Any]] = None) -> list[str]:
    """Short lines for st.caption / st.info on benefit pages."""
    meta = meta or {}
    cm = policy_cache_meta()
    size = meta.get("cache_size", cm["cache_size"])
    age_text = meta.get("cache_age_text") or cm["cache_age_text"]
    source = meta.get("data_source") or (
        "로컬 폴백 가능" if cm["empty"] else "온통청년 정책 캐시"
    )
    is_fb = meta.get("is_fallback")
    if is_fb is None:
        is_fb = "폴백" in str(source)
    lines = [
        f"**출처:** {source}",
        f"**캐시:** {int(size or 0):,}건 · 갱신 {age_text}",
        f"**방법:** {BENEFITS_METHOD}",
        f"**한계:** {BENEFITS_DISCLAIMER}",
    ]
    if is_fb or cm["empty"]:
        lines.append(
            "**주의:** 폴백/빈 캐시 상태 — **7_청년혜택업데이트**에서 정책을 동기화하세요."
        )
    return lines


def benefits_trust_markdown(meta: Optional[dict[str, Any]] = None) -> str:
    return "\n\n".join(benefits_trust_lines(meta))


def stats_provenance(db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """DB path + last KOSIS core sync age for page 6 / AI."""
    from .gunsan_stats import resolve_db_path, list_db_tables

    path = resolve_db_path(db_path)
    age = None
    try:
        from .kosis_sync import last_core_sync_age_seconds

        age = last_core_sync_age_seconds(path)
    except Exception:
        age = None
    return {
        "db_path": str(path),
        "db_exists": path.is_file(),
        "table_count": len(list_db_tables(path)) if path.is_file() else 0,
        "core_sync_age_seconds": age,
        "core_sync_age_text": format_age_seconds(age),
        "method": STATS_METHOD,
        "disclaimer": STATS_DISCLAIMER,
        "limitations": list(STATS_LIMITATIONS),
    }


def enrich_stat_result(result: dict[str, Any], db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """Attach fixed trust fields to get_gunsan_stat output (AI tool + page)."""
    out = dict(result or {})
    prov = stats_provenance(db_path)
    out["method"] = STATS_METHOD
    out["disclaimer"] = STATS_DISCLAIMER
    out["limitations"] = list(STATS_LIMITATIONS)
    out["db_path"] = prov["db_path"]
    out["core_sync_age_text"] = prov["core_sync_age_text"]
    out["core_sync_age_seconds"] = prov["core_sync_age_seconds"]
    return out


def stats_trust_lines(prov: Optional[dict[str, Any]] = None) -> list[str]:
    prov = prov or stats_provenance()
    lines = [
        f"**DB:** `{prov.get('db_path')}`"
        + (" (존재)" if prov.get("db_exists") else " (**파일 없음**)"),
        f"**KOSIS 핵심 동기화:** {prov.get('core_sync_age_text')}",
        f"**방법:** {STATS_METHOD}",
        f"**한계:** {STATS_DISCLAIMER}",
    ]
    return lines


def stats_trust_markdown(prov: Optional[dict[str, Any]] = None) -> str:
    return "\n\n".join(stats_trust_lines(prov))
