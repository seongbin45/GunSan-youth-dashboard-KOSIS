"""
Maintain gunsan_youth_data.db from KOSIS — process recorded in
Technical_document/What we talked about with AI/pages/4_&_5_pages.txt

Steps (same as manual collection history):
  1. List 군산시청년통계 root V_3_214_005
  2. List each of 6 domains → table catalog CSVs/tables
  3. Pull core numeric tables via statisticsParameterData (orgId=712)
  4. Write/replace SQLite tables used by gunsan_stats + page 6

Does NOT hardcode secrets; requires KOSIS_API_KEY in secrets/env.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .config import GUNSAN_STATS_DB_PATH, GUNSAN_STATS_SYNC_TTL_SECONDS
from .kosis_client import KosisApiError, KosisClient

logger = logging.getLogger(__name__)

# Root catalog from documentation
GUNSAN_YOUTH_ROOT_LIST_ID = "V_3_214_005"

# Domain folders under 군산시청년통계
DOMAIN_LIST_IDS = {
    "population": "V_3_214_005_001",  # 인구·가구
    "economy": "V_3_214_005_002",     # 경제
    "job": "V_3_214_005_003",         # 일자리
    "startup": "V_3_214_005_004",     # 창업
    "welfare": "V_3_214_005_005",     # 복지
    "health": "V_3_214_005_006",      # 건강
}

# Core numeric pulls used by AI get_gunsan_youth_stats (documented successful params)
# itmId trailing space matches the working KOSIS shared URL pattern in the log.
CORE_DATA_SPECS: dict[str, dict[str, Any]] = {
    "gunsan_youth_population_success": {
        "orgId": "712",
        "tblId": "DT_712005_2024A001",
        "itmId": "T001 ",
        "objL1": "A01 A02 A03",
        "objL2": "B02 B03",
        "prdSe": "F",
        "newEstPrdCnt": "3",
        "description": "전북 시·군별 청년인구",
    },
    "gunsan_youth_housing_data": {
        "orgId": "712",
        "tblId": "DT_712005_2024B001",
        "itmId": "T001 ",
        "objL1": "A01 A02 A03",
        "objL2": "B02 B03",
        "prdSe": "F",
        "newEstPrdCnt": "3",
        "description": "소유 건수별 주택 소유 인구",
    },
    "gunsan_youth_wage_data": {
        "orgId": "712",
        "tblId": "DT_712005_2024C005",
        "itmId": "T001 ",
        "objL1": "A01 A02 A03",
        "objL2": "B02 B03",
        "prdSe": "F",
        "newEstPrdCnt": "3",
        "description": "취업자의 월평균 임금",
    },
    "gunsan_youth_health_data": {
        "orgId": "712",
        "tblId": "DT_712005_2024F005",
        "itmId": "T001 ",
        "objL1": "A01 A02 A03",
        "objL2": "B02 B03",
        "prdSe": "F",
        "newEstPrdCnt": "3",
        "description": "건강지표",
    },
}

DOMAIN_CATALOG_TABLE = {
    "population": "gunsan_population_tables",
    "economy": "gunsan_economy_tables",
    "job": "gunsan_job_tables",
    "startup": "gunsan_startup_tables",
    "welfare": "gunsan_welfare_tables",
    "health": "gunsan_health_tables",
}


def _db_path(path: Optional[str | Path] = None) -> Path:
    return Path(path) if path else Path(GUNSAN_STATS_DB_PATH)


def _ensure_meta(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kosis_sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    _ensure_meta(conn)
    conn.execute(
        """
        INSERT INTO kosis_sync_meta(key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (key, json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value, int(time.time())),
    )
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str) -> Any | None:
    _ensure_meta(conn)
    row = conn.execute(
        "SELECT value FROM kosis_sync_meta WHERE key=?", (key,)
    ).fetchone()
    if not row:
        return None
    raw = row[0]
    try:
        return json.loads(raw)
    except Exception:
        return raw


def last_core_sync_age_seconds(db_path: Optional[str | Path] = None) -> int | None:
    path = _db_path(db_path)
    if not path.is_file():
        return None
    conn = sqlite3.connect(str(path))
    try:
        _ensure_meta(conn)
        row = conn.execute(
            "SELECT updated_at FROM kosis_sync_meta WHERE key=?",
            ("core_sync_completed_at",),
        ).fetchone()
        if not row:
            return None
        return int(time.time()) - int(row[0])
    finally:
        conn.close()


def needs_core_sync(db_path: Optional[str | Path] = None, ttl: Optional[int] = None) -> bool:
    ttl = GUNSAN_STATS_SYNC_TTL_SECONDS if ttl is None else ttl
    if ttl <= 0:
        return False
    age = last_core_sync_age_seconds(db_path)
    if age is None:
        return True
    return age > ttl


def _write_df(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    df.to_sql(table, conn, if_exists="replace", index=False)
    return len(df)


def sync_catalog(client: Optional[KosisClient] = None, db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """Refresh list tables (root + 6 domains) into gunsan_youth_data.db."""
    client = client or KosisClient()
    path = _db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    results: dict[str, Any] = {"tables": {}, "errors": []}
    try:
        root = client.fetch_list(GUNSAN_YOUTH_ROOT_LIST_ID)
        n = _write_df(conn, "gunsan_youth_list", pd.DataFrame(root))
        results["tables"]["gunsan_youth_list"] = n

        for domain, list_id in DOMAIN_LIST_IDS.items():
            try:
                rows = client.fetch_list(list_id)
                table = DOMAIN_CATALOG_TABLE[domain]
                n = _write_df(conn, table, pd.DataFrame(rows))
                results["tables"][table] = n
            except Exception as e:
                logger.exception("catalog sync failed %s", domain)
                results["errors"].append({"domain": domain, "error": str(e)})

        set_meta(conn, "catalog_sync_completed_at", int(time.time()))
        set_meta(conn, "catalog_sync_result", results)
        return {"ok": not results["errors"], **results}
    finally:
        conn.close()


def sync_core_tables(
    client: Optional[KosisClient] = None,
    db_path: Optional[str | Path] = None,
    only: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Refresh core numeric tables used by gunsan_stats / AI.
    also mirrors population into gunsan_youth_population_debug for compatibility.
    """
    client = client or KosisClient()
    path = _db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    results: dict[str, Any] = {"tables": {}, "errors": []}
    specs = CORE_DATA_SPECS
    if only:
        specs = {k: v for k, v in specs.items() if k in only}

    try:
        for table_name, spec in specs.items():
            try:
                rows = client.fetch_parameter_data(
                    org_id=spec["orgId"],
                    tbl_id=spec["tblId"],
                    itm_id=spec.get("itmId", "T001 "),
                    obj_l1=spec.get("objL1", "A01 A02 A03"),
                    obj_l2=spec.get("objL2", "B02 B03"),
                    prd_se=spec.get("prdSe", "F"),
                    new_est_prd_cnt=spec.get("newEstPrdCnt", "3"),
                )
                df = pd.DataFrame(rows)
                n = _write_df(conn, table_name, df)
                results["tables"][table_name] = {
                    "rows": n,
                    "tblId": spec["tblId"],
                    "description": spec.get("description"),
                }
                if table_name == "gunsan_youth_population_success" and n:
                    _write_df(conn, "gunsan_youth_population_debug", df)
                    results["tables"]["gunsan_youth_population_debug"] = {"rows": n, "mirror": True}
            except Exception as e:
                logger.exception("core sync failed %s", table_name)
                results["errors"].append({"table": table_name, "error": str(e)})

        set_meta(conn, "core_sync_completed_at", int(time.time()))
        set_meta(conn, "core_sync_result", results)
        return {"ok": len(results["errors"]) == 0, **results}
    finally:
        conn.close()


def sync_all(client: Optional[KosisClient] = None, db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """Catalog + core numeric tables."""
    cat = sync_catalog(client=client, db_path=db_path)
    core = sync_core_tables(client=client, db_path=db_path)
    return {
        "ok": cat.get("ok") and core.get("ok"),
        "catalog": cat,
        "core": core,
        "db_path": str(_db_path(db_path)),
    }


def ensure_fresh_core(
    db_path: Optional[str | Path] = None,
    ttl: Optional[int] = None,
    client: Optional[KosisClient] = None,
) -> dict[str, Any]:
    """
    If core data is missing or older than TTL and API key is set, refresh.
    Safe to call from UI; never raises on missing key (returns skipped).
    """
    from .config import KOSIS_API_KEY

    if not (KOSIS_API_KEY or "").strip():
        return {"ok": False, "skipped": True, "reason": "KOSIS_API_KEY not set"}
    if not needs_core_sync(db_path=db_path, ttl=ttl):
        return {
            "ok": True,
            "skipped": True,
            "reason": "within TTL",
            "age_seconds": last_core_sync_age_seconds(db_path),
        }
    try:
        return {"skipped": False, **sync_core_tables(client=client or KosisClient(), db_path=db_path)}
    except Exception as e:
        return {"ok": False, "skipped": False, "error": str(e)}


def core_freshness_status(
    db_path: Optional[str | Path] = None,
    ttl: Optional[int] = None,
) -> dict[str, Any]:
    """
    Read-only freshness snapshot for UI / CLI (no network).

    Returns:
      stale, age_seconds, age_text, ttl_seconds, ttl_days, db_path, summary
    """
    from .trust_copy import format_age_seconds

    ttl_s = GUNSAN_STATS_SYNC_TTL_SECONDS if ttl is None else int(ttl)
    age = last_core_sync_age_seconds(db_path)
    stale = needs_core_sync(db_path=db_path, ttl=ttl_s)
    path = _db_path(db_path)
    ttl_days = max(0, ttl_s // 86400) if ttl_s > 0 else 0
    if age is None:
        summary = (
            f"KOSIS 핵심 동기화 기록 없음 · TTL {ttl_days}일 기준 갱신 권장"
            if stale
            else f"동기화 기록 없음 · TTL 검사 비활성(ttl={ttl_s})"
        )
    elif stale:
        summary = (
            f"KOSIS 핵심 통계가 TTL({ttl_days}일)보다 오래됨 "
            f"(age≈{format_age_seconds(age)}) · 6페이지에서 갱신 권장"
        )
    else:
        summary = (
            f"KOSIS 핵심 통계 신선 · TTL {ttl_days}일 이내 "
            f"(마지막 동기화 {format_age_seconds(age)})"
        )
    return {
        "stale": stale,
        "age_seconds": age,
        "age_text": format_age_seconds(age),
        "ttl_seconds": ttl_s,
        "ttl_days": ttl_days,
        "db_path": str(path),
        "db_exists": path.is_file(),
        "summary": summary,
    }
