"""
GunSan youth stats from local SQLite (same DB as pages/6_군산시 청년 데이터.py).

Single source of truth:
- AI tool get_gunsan_youth_stats → get_gunsan_stat()
- Page 6 charts → load_dashboard_data()
Both read the same DEFAULT_DB and the same table name constants.
No invented numbers when DB is present; missing tables are reported explicitly.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

# Project root: finfit_youth/../
_ROOT = Path(__file__).resolve().parents[1]
try:
    from .config import GUNSAN_STATS_DB_PATH
    DEFAULT_DB = Path(GUNSAN_STATS_DB_PATH)
    if not DEFAULT_DB.is_absolute():
        DEFAULT_DB = _ROOT / DEFAULT_DB
except Exception:
    DEFAULT_DB = _ROOT / "gunsan_youth_data.db"

# Logical name → physical SQLite table (page 6 + AI employment/housing sources)
DASHBOARD_TABLES: dict[str, str] = {
    "housing": "gunsan_youth_housing_data",
    "wage": "gunsan_youth_wage_data",
    "health": "gunsan_youth_health_data",
    "population_success": "gunsan_youth_population_success",
    "population_debug": "gunsan_youth_population_debug",
    "difficulty": "전북특별자치도_취업의_어려움_사회조사_20221231",
    "room": "전북특별자치도_군산시_원룸_및_오피스텔_현황_20260203",
    "job": "전북특별자치도_연령별취업자_20211231",
    "saving": "서민금융진흥원_청년도약계좌_취급은행_현황_20250731",
}

# AI / get_gunsan_stat categories (employment is a documented bundle of two metrics)
STAT_CATEGORIES = (
    "population",
    "housing",
    "income",
    "employment",  # bundle: difficulty + count (backward compatible)
    "employment_difficulty",  # 군산 사회조사 — 어려움 요인 %
    "employment_count",  # 전북 연령별취업자 — 분기평균 취업자 규모
)

# Youth age labels in 연령별취업자 table (not the same as 18~39 pop table)
_JOB_YOUTH_AGES = ("15~19세", "20~24세", "25~29세", "30~34세", "35~39세")

# Only used if DB missing/unreadable (honest fallback, labeled)
_FALLBACK = {
    "population": {
        "data": "DB 없음 — 참고값: 군산 청년(18~39세) 약 56,117명 (과거 KOSIS 정리본)",
        "source": "fallback (gunsan_youth_data.db 없음)",
        "insight": "로컬 DB를 확인하세요. 6_군산시 청년 데이터 페이지와 동일 파일을 사용합니다.",
        "from_db": False,
    },
    "employment": {
        "data": "DB 없음 — 군산 취업 어려움 조사 / 전북 연령별 취업자 표를 불러오지 못함",
        "source": "fallback",
        "insight": "employment_difficulty·employment_count 표를 확인하세요.",
        "from_db": False,
    },
    "employment_difficulty": {
        "data": "DB 없음 — 군산시 취업 어려움 사회조사 표를 불러오지 못함",
        "source": "fallback",
        "insight": "전북특별자치도_취업의_어려움_사회조사 테이블 필요.",
        "from_db": False,
    },
    "employment_count": {
        "data": "DB 없음 — 전북 연령별 취업자 표를 불러오지 못함",
        "source": "fallback",
        "insight": "전북특별자치도_연령별취업자 테이블 필요. (전북 단위, 군산 단독 아님)",
        "from_db": False,
    },
    "housing": {
        "data": "DB 없음 — 참고: 청년 주택 소유 비율은 전체보다 낮은 편",
        "source": "fallback",
        "insight": "gunsan_youth_housing_data 테이블을 사용하세요.",
        "from_db": False,
    },
    "income": {
        "data": "DB 없음 — 참고: 청년 월평균 임금 구간 분포는 wage 테이블 기준",
        "source": "fallback",
        "insight": "gunsan_youth_wage_data 테이블을 사용하세요.",
        "from_db": False,
    },
}


def resolve_db_path(db_path: Optional[str | Path] = None) -> Path:
    """Absolute path to gunsan_youth_data.db (config or default)."""
    path = Path(db_path) if db_path else DEFAULT_DB
    if not path.is_absolute():
        path = _ROOT / path
    return path


def _connect(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def list_db_tables(db_path: Optional[str | Path] = None) -> list[str]:
    """All table names in the stats DB (sorted). Empty if DB missing."""
    path = resolve_db_path(db_path)
    if not path.is_file():
        return []
    conn = sqlite3.connect(str(path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def read_table(
    logical_or_physical: str,
    db_path: Optional[str | Path] = None,
) -> "Any":  # pandas.DataFrame
    """
    Read one table as a DataFrame.
    `logical_or_physical` may be a DASHBOARD_TABLES key or a raw table name.
    Raises FileNotFoundError / ValueError / RuntimeError with clear messages.
    """
    import pandas as pd

    physical = DASHBOARD_TABLES.get(logical_or_physical, logical_or_physical)
    path = resolve_db_path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"stats DB not found: {path}")
    conn = sqlite3.connect(str(path))
    try:
        if not _table_exists(conn, physical):
            raise ValueError(f"table not found: {physical}")
        return pd.read_sql_query(f'SELECT * FROM "{physical}"', conn)
    finally:
        conn.close()


def load_dashboard_data(db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """
    Single loader for page 6 (and any chart UI).

    Returns:
      db_path, available_tables,
      tables: {logical_key: DataFrame}  (missing → empty DataFrame),
      missing: [logical keys not in DB],
      errors: {logical_key: str},
      ok: True if DB file exists
    """
    import pandas as pd

    path = resolve_db_path(db_path)
    out: dict[str, Any] = {
        "db_path": str(path),
        "ok": path.is_file(),
        "available_tables": [],
        "tables": {},
        "missing": [],
        "errors": {},
    }
    if not path.is_file():
        out["errors"]["_db"] = f"DB file missing: {path}"
        for key in DASHBOARD_TABLES:
            out["tables"][key] = pd.DataFrame()
            out["missing"].append(key)
        return out

    out["available_tables"] = list_db_tables(path)
    for key, physical in DASHBOARD_TABLES.items():
        try:
            if physical not in out["available_tables"]:
                out["tables"][key] = pd.DataFrame()
                out["missing"].append(key)
                out["errors"][key] = f"table missing: {physical}"
                continue
            out["tables"][key] = read_table(key, path)
        except Exception as e:
            out["tables"][key] = pd.DataFrame()
            out["missing"].append(key)
            out["errors"][key] = str(e)
    return out


def _fmt_num(n: float | int) -> str:
    try:
        if isinstance(n, float) and not n.is_integer():
            return f"{n:,.1f}"
        return f"{int(n):,}"
    except Exception:
        return str(n)


def _population(conn: sqlite3.Connection) -> dict[str, Any]:
    # Prefer success table, then debug (same keys as DASHBOARD_TABLES)
    for table in (
        DASHBOARD_TABLES["population_success"],
        DASHBOARD_TABLES["population_debug"],
    ):
        if not _table_exists(conn, table):
            continue
        rows = conn.execute(
            f'SELECT C1_NM, C2_NM, DT, PRD_DE, TBL_NM, UNIT_NM FROM "{table}"'
        ).fetchall()
        by_region = {str(r["C1_NM"]): float(r["DT"]) for r in rows if r["DT"] is not None}
        youth = by_region.get("군산시")
        jeonbuk = by_region.get("전북")
        nation = by_region.get("전국")
        year = rows[0]["PRD_DE"] if rows else "?"
        tbl = rows[0]["TBL_NM"] if rows else table
        if youth is None:
            continue
        # Total city pop from dong table if available
        total = None
        dong = "군산시_읍면동별__연령_5세단위_별_한국인_현황_20260404193059"
        if _table_exists(conn, dong):
            # Row with 합계 — first column age label, second is total count string
            r = conn.execute(
                f'SELECT * FROM "{dong}" WHERE "O_2 연령별(1)" LIKE ? LIMIT 1',
                ("%합계%",),
            ).fetchone()
            if r is not None:
                # columns: O_2..., Y2024... first data col is total
                keys = r.keys()
                # index 1 is often 군산시 계
                try:
                    total = int(str(r[1]).replace(",", ""))
                except Exception:
                    total = None
        share = None
        if total and total > 0:
            share = youth / total * 100
            data = (
                f"군산시 청년(18~39세) {_fmt_num(youth)}명"
                f"{f' / 전체 인구 약 {_fmt_num(total)}명 (청년 비중 약 {share:.1f}%)' if total else ''}"
            )
        else:
            data = f"군산시 청년(18~39세) {_fmt_num(youth)}명"
            if jeonbuk:
                data += f" · 전북 청년 {_fmt_num(jeonbuk)}명"
            if nation:
                data += f" · 전국 청년 {_fmt_num(nation)}명"

        insight_parts = []
        if jeonbuk and youth:
            insight_parts.append(f"전북 청년 대비 군산 비중 약 {youth/jeonbuk*100:.1f}%")
        if share is not None:
            insight_parts.append(f"시 전체 대비 청년 약 {share:.1f}%")
        return {
            "category": "population",
            "data": data,
            "source": f"gunsan_youth_data.db · {table} · {tbl} · {year}",
            "insight": " · ".join(insight_parts) or "KOSIS 기반 로컬 DB 수치",
            "from_db": True,
            "figures": {
                "gunsan_youth_18_39": youth,
                "jeonbuk_youth": jeonbuk,
                "korea_youth": nation,
                "gunsan_total_approx": total,
                "youth_share_pct": round(share, 2) if share is not None else None,
                "year": year,
            },
        }
    raise RuntimeError("population tables missing or empty")


def _housing(conn: sqlite3.Connection) -> dict[str, Any]:
    table = DASHBOARD_TABLES["housing"]
    if not _table_exists(conn, table):
        raise RuntimeError("housing table missing")
    rows = conn.execute(
        f'SELECT C1_NM, C2_NM, DT, PRD_DE, TBL_NM, UNIT_NM FROM "{table}"'
    ).fetchall()
    youth_rate = total_rate = youth_owners = None
    year = rows[0]["PRD_DE"] if rows else "?"
    tbl = rows[0]["TBL_NM"] if rows else table
    # Prefer 18~39 band over 15~29 when both exist
    for r in rows:
        c1, c2, dt = str(r["C1_NM"]), str(r["C2_NM"]), r["DT"]
        if "전체" in c1 and "비율" in c2:
            total_rate = float(dt)
        if "18~39" in c1 and "비율" in c2:
            youth_rate = float(dt)
        if "18~39" in c1 and "인구" in c2:
            youth_owners = float(dt)
    if youth_rate is None or youth_owners is None:
        for r in rows:
            c1, c2, dt = str(r["C1_NM"]), str(r["C2_NM"]), r["DT"]
            if youth_rate is None and "청년" in c1 and "비율" in c2:
                youth_rate = float(dt)
            if youth_owners is None and "청년" in c1 and "인구" in c2:
                youth_owners = float(dt)
    if youth_rate is None and youth_owners is None:
        raise RuntimeError("no youth housing figures")
    parts = []
    if youth_rate is not None:
        parts.append(f"군산 청년(18~39세) 주택소유비율 {youth_rate}%")
    if total_rate is not None:
        parts.append(f"시 전체 소유비율 {total_rate}%")
    if youth_owners is not None:
        parts.append(f"청년 주택소유 인구 약 {_fmt_num(youth_owners)}")
    insight = "청년 소유 비율이 전체보다 낮으면 주거 지원 정책 수요가 클 수 있음."
    if youth_rate is not None and total_rate is not None and youth_rate < total_rate:
        insight = (
            f"청년 소유비율({youth_rate}%)이 시 전체({total_rate}%)보다 낮아 "
            "전세·월세 지원 체감 수요가 클 수 있음."
        )
    return {
        "category": "housing",
        "data": " · ".join(parts),
        "source": f"gunsan_youth_data.db · {table} · {tbl} · {year}",
        "insight": insight,
        "from_db": True,
        "figures": {
            "youth_ownership_rate_pct": youth_rate,
            "total_ownership_rate_pct": total_rate,
            "youth_owner_population": youth_owners,
            "year": year,
        },
    }


def _income(conn: sqlite3.Connection) -> dict[str, Any]:
    table = DASHBOARD_TABLES["wage"]
    if not _table_exists(conn, table):
        raise RuntimeError("wage table missing")
    rows = conn.execute(
        f'SELECT C1_NM, C2_NM, DT, PRD_DE, TBL_NM, UNIT_NM FROM "{table}" '
        f'WHERE C1_NM LIKE ?',
        ("%청년%",),
    ).fetchall()
    if not rows:
        rows = conn.execute(
            f'SELECT C1_NM, C2_NM, DT, PRD_DE, TBL_NM, UNIT_NM FROM "{table}"'
        ).fetchall()
    year = rows[0]["PRD_DE"] if rows else "?"
    tbl = rows[0]["TBL_NM"] if rows else table
    bands = []
    for r in rows:
        if "청년" not in str(r["C1_NM"]):
            continue
        bands.append((str(r["C2_NM"]), float(r["DT"])))
    if not bands:
        raise RuntimeError("no youth wage bands")
    # DT unit is often '천명' (thousands of persons)
    desc = ", ".join(f"{name} {val}" for name, val in bands[:6])
    data = (
        f"군산 청년(18~39세) 취업자 월평균 임금 구간 분포(단위: 천명 규모): {desc}"
    )
    low = sum(v for n, v in bands if "200" in n or "100만" in n or "미만" in n)
    return {
        "category": "income",
        "data": data,
        "source": f"gunsan_youth_data.db · {table} · {tbl} · {year}",
        "insight": (
            "저임금 구간에 청년 취업자가 있으면 자산형성·주거 지원 혜택 체감도가 커질 수 있음."
        ),
        "from_db": True,
        "figures": {
            "bands": [{"label": n, "value_thousand_persons": v} for n, v in bands],
            "year": year,
        },
    }


def _employment_difficulty(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    군산시 행 — 전북 사회조사 '취업의 어려움' 요인 비율(%).
    지리: 군산시 / 지표: 응답 비율 / 연령: 조사 정의(청년 사회조사 맥락)
    """
    table = DASHBOARD_TABLES["difficulty"]
    if not _table_exists(conn, table):
        raise RuntimeError("employment difficulty table missing")
    r = conn.execute(
        f'SELECT * FROM "{table}" WHERE 특성별2 = ? LIMIT 1',
        ("군산시",),
    ).fetchone()
    if not r:
        raise RuntimeError("no Gunsan row in difficulty survey")

    exclude = {"특성별1", "특성별2", "소계", "계"}
    reasons: list[tuple[str, float]] = []
    for k in r.keys():
        if k in exclude or str(k).startswith("Unnamed"):
            continue
        try:
            reasons.append((str(k), float(r[k])))
        except Exception:
            continue
    reasons.sort(key=lambda x: -x[1])
    if not reasons:
        raise RuntimeError("no difficulty percentages")

    top = reasons[0]
    data = f"군산시 취업 어려움 조사(사회조사): 1위 '{top[0]}' {top[1]}%"
    if len(reasons) > 1:
        data += f", 2위 '{reasons[1][0]}' {reasons[1][1]}%"
    if len(reasons) > 2:
        data += f", 3위 '{reasons[2][0]}' {reasons[2][1]}%"

    return {
        "category": "employment_difficulty",
        "data": data,
        "source": f"gunsan_youth_data.db · {table} · 특성별2=군산시",
        "insight": (
            "군산 응답 비율(%)이다. 전북 취업자 수(employment_count)와 단위·지역이 다르다."
        ),
        "from_db": True,
        "metric": {
            "id": "employment_difficulty",
            "geography": "군산시",
            "unit": "percent",
            "age_band": "사회조사 정의(표 원문)",
            "table": table,
        },
        "figures": {
            "difficulty_all": [{"reason": a, "pct": b} for a, b in reasons],
            "difficulty_top": [{"reason": a, "pct": b} for a, b in reasons[:3]],
            "none_or_other": {
                "어려움이 없었음": next((b for a, b in reasons if "없었" in a), None),
                "기타": next((b for a, b in reasons if a == "기타"), None),
            },
        },
    }


def _employment_count(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    전북 연령별 취업자 수.

    중요(정확성):
    - 표는 성별(남/여) × 분기(1~4) 로 쪼개져 있음.
    - 단순 SUM(취업자수)은 분기·성별을 중복 합산하므로 사용하지 않음.
    - 방법: 각 분기마다 남+여 합 → 4개 분기의 산술평균 = 연간 대표값.
    - 지리: 전북 전체 (군산시 단독 수치 아님).
    - 연령: 15~39세 합 (인구 표 18~39와 다를 수 있음).
    - 단위: 원 자료 `취업자수` 그대로 (통상 천명 규모 — 표에 단위 컬럼 없음).
    """
    table = DASHBOARD_TABLES["job"]
    if not _table_exists(conn, table):
        raise RuntimeError("employment count table missing")

    years = conn.execute(
        f'SELECT DISTINCT 연도 FROM "{table}" ORDER BY 연도 DESC LIMIT 1'
    ).fetchone()
    if not years:
        raise RuntimeError("no year in job table")
    y = years[0]

    quarters = [
        r[0]
        for r in conn.execute(
            f'SELECT DISTINCT 분기 FROM "{table}" WHERE 연도=? ORDER BY 분기',
            (y,),
        ).fetchall()
    ]
    if not quarters:
        raise RuntimeError("no quarters in job table")

    # quarter → youth total (남+여, 15~39)
    q_totals: list[tuple[str, float]] = []
    by_age_avg: dict[str, float] = {a: 0.0 for a in _JOB_YOUTH_AGES}
    age_q_vals: dict[str, list[float]] = {a: [] for a in _JOB_YOUTH_AGES}

    for q in quarters:
        q_sum = 0.0
        for age in _JOB_YOUTH_AGES:
            row = conn.execute(
                f'SELECT SUM(취업자수) FROM "{table}" '
                f"WHERE 연도=? AND 분기=? AND 연령=? AND 성별 IN ('남자','여자')",
                (y, q, age),
            ).fetchone()
            v = float(row[0] or 0)
            q_sum += v
            age_q_vals[age].append(v)
        q_totals.append((str(q), q_sum))

    if not q_totals:
        raise RuntimeError("empty quarterly totals")

    youth_avg = sum(t for _, t in q_totals) / len(q_totals)
    for age, vals in age_q_vals.items():
        by_age_avg[age] = (sum(vals) / len(vals)) if vals else 0.0

    # all ages annual avg for share (same method)
    all_q = []
    for q in quarters:
        row = conn.execute(
            f'SELECT SUM(취업자수) FROM "{table}" '
            f"WHERE 연도=? AND 분기=? AND 성별 IN ('남자','여자')",
            (y, q),
        ).fetchone()
        all_q.append(float(row[0] or 0))
    total_avg = sum(all_q) / len(all_q) if all_q else 0.0
    share = (youth_avg / total_avg * 100.0) if total_avg > 0 else None

    data = (
        f"전북 연령별 취업자(연도 {y}): 15~39세 분기평균 약 {_fmt_num(youth_avg)} "
        f"(남+여, 분기별 합의 평균 · 원표 `취업자수` · 단위 컬럼 없음, 통상 천명 규모)"
    )
    if share is not None:
        data += f" · 전 연령 대비 청년 비중 약 {share:.1f}%"
    data += (
        " · ※ 전북 전체 수치이며 군산시 단독이 아님. "
        "인구 표(18~39)와 연령 정의가 다를 수 있음."
    )

    return {
        "category": "employment_count",
        "data": data,
        "source": f"gunsan_youth_data.db · {table} · 연도 {y}",
        "insight": (
            "중복 합산 방지: 성별·분기를 한꺼번에 SUM하지 않고, "
            "분기마다 남+여 합 후 연평균한다. "
            "수치 단위는 원표에 명시되지 않음(통상 천명 규모로 읽음)."
        ),
        "from_db": True,
        "metric": {
            "id": "employment_count",
            "geography": "전북특별자치도(전체)",
            # UI-friendly label; do not invent a unit the table does not print
            "unit": "원표_취업자수(통상_천명_규모)",
            "unit_label_ko": "원표 `취업자수` (단위 컬럼 없음 · 통상 천명 규모)",
            "unit_note": (
                "표에 단위 컬럼 없음. 한국 고용통계(연령별취업자)에서 흔히 천명 — "
                "원문·메타 확인 권장. 인위적으로 '명'으로 단정하지 않음."
            ),
            "age_band": "15~39세",
            "aggregation": "quarterly_mean_of_male_plus_female",
            "year": y,
            "table": table,
        },
        "figures": {
            "year": y,
            "youth_15_39_quarterly_mean": youth_avg,
            "all_ages_quarterly_mean": total_avg,
            "youth_share_pct": round(share, 2) if share is not None else None,
            "by_quarter_youth": [{"quarter": q, "value": v} for q, v in q_totals],
            "by_age_quarterly_mean": [
                {"age": a, "value": by_age_avg[a]} for a in _JOB_YOUTH_AGES
            ],
            # deprecated wrong field name kept absent on purpose
        },
    }


def _employment(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    Backward-compatible bundle: difficulty (Gunsan %) + count (Jeonbuk scale).
    Explicitly separates the two metrics so AI/UI do not confuse them.
    """
    parts: list[str] = []
    sources: list[str] = []
    figures: dict[str, Any] = {"bundle": True}
    metrics_meta: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        d = _employment_difficulty(conn)
        parts.append("[군산·어려움%] " + d["data"])
        sources.append(d.get("source") or "")
        figures["difficulty"] = d.get("figures")
        metrics_meta.append(d.get("metric") or {})
    except Exception as e:
        errors.append(f"difficulty: {e}")

    try:
        c = _employment_count(conn)
        parts.append("[전북·취업자수] " + c["data"])
        sources.append(c.get("source") or "")
        figures["count"] = c.get("figures")
        # legacy-friendly aliases (correct aggregation)
        fig_c = c.get("figures") or {}
        figures["jeonbuk_youth_employed_quarterly_mean"] = fig_c.get(
            "youth_15_39_quarterly_mean"
        )
        figures["employment_year"] = fig_c.get("year")
        metrics_meta.append(c.get("metric") or {})
    except Exception as e:
        errors.append(f"count: {e}")

    if not parts:
        raise RuntimeError("employment tables empty: " + "; ".join(errors))

    return {
        "category": "employment",
        "data": " · ".join(parts),
        "source": " · ".join(s for s in sources if s),
        "insight": (
            "두 지표를 섞어 해석하지 말 것: "
            "(1) 군산 어려움 응답% (2) 전북 취업자 규모(분기평균). "
            "단일 지표가 필요하면 employment_difficulty 또는 employment_count 를 사용."
        ),
        "from_db": True,
        "metric": {
            "id": "employment_bundle",
            "components": metrics_meta,
            "note": "composite",
        },
        "figures": figures,
        "load_notes": errors or None,
    }


def get_gunsan_stat(category: str, db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """
    category:
      population | housing | income |
      employment (bundle) | employment_difficulty | employment_count

    Always attaches disclaimer / sync provenance via trust_copy (AI + page 6).
    """
    from .trust_copy import enrich_stat_result

    cat = (category or "").strip().lower()
    if cat not in STAT_CATEGORIES:
        return enrich_stat_result(
            {
                "error": (
                    f"알 수 없는 카테고리: {category}. "
                    f"허용: {', '.join(STAT_CATEGORIES)}"
                ),
                "from_db": False,
                "category": cat,
            },
            db_path,
        )

    path = resolve_db_path(db_path)
    if not path.is_file():
        fb = dict(_FALLBACK.get(cat) or _FALLBACK["employment"])
        fb["category"] = cat
        return enrich_stat_result(fb, path)

    try:
        conn = _connect(path)
        try:
            if cat == "population":
                raw = _population(conn)
            elif cat == "housing":
                raw = _housing(conn)
            elif cat == "income":
                raw = _income(conn)
            elif cat == "employment_difficulty":
                raw = _employment_difficulty(conn)
            elif cat == "employment_count":
                raw = _employment_count(conn)
            else:
                raw = _employment(conn)
            return enrich_stat_result(raw, path)
        finally:
            conn.close()
    except Exception as e:
        fb = dict(_FALLBACK.get(cat) or _FALLBACK["employment"])
        fb["category"] = cat
        fb["data"] = fb["data"] + f" (로드 오류: {e})"
        fb["error_detail"] = str(e)
        return enrich_stat_result(fb, path)
