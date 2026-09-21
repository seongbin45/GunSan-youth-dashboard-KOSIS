"""
Rebuild / refresh gunsan_youth_data.db.

Historical process (CSV → sqlite) is documented in:
  Technical_document/What we talked about with AI/pages/4_&_5_pages.txt

Current preferred path: live KOSIS Open API → SQLite (finfit_youth.kosis_sync).

Usage:
  set KOSIS_API_KEY=...
  python KOSIS_Database_Creation_Code/make_database.py
  python KOSIS_Database_Creation_Code/make_database.py --core-only
  python KOSIS_Database_Creation_Code/make_database.py --from-csv   # legacy CSV import
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.config import GUNSAN_STATS_DB_PATH, KOSIS_API_KEY
from finfit_youth.kosis_sync import sync_all, sync_core_tables


def import_from_csv(db_path: Path, csv_dir: Path) -> None:
    """Legacy path from the original conversation (CSV → tables)."""
    mapping = {
        "gunsan_youth_population_success": "gunsan_youth_population_success.csv",
        "gunsan_youth_housing_data": "gunsan_youth_housing_data.csv",
        "gunsan_youth_wage_data": "gunsan_youth_wage_data.csv",
        "gunsan_youth_health_data": "gunsan_youth_health_data.csv",
    }
    conn = sqlite3.connect(str(db_path))
    try:
        for table, fname in mapping.items():
            fpath = csv_dir / fname
            if not fpath.is_file():
                # also try project .csv/
                alt = ROOT / ".csv" / fname
                fpath = alt if alt.is_file() else fpath
            if not fpath.is_file():
                print(f"skip missing {fname}")
                continue
            df = pd.read_csv(fpath)
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"imported {fname} → {table} ({len(df)} rows)")
            if table == "gunsan_youth_population_success":
                df.to_sql("gunsan_youth_population_debug", conn, if_exists="replace", index=False)
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync GunSan youth stats DB from KOSIS or CSV")
    parser.add_argument("--db", default=str(ROOT / GUNSAN_STATS_DB_PATH))
    parser.add_argument("--core-only", action="store_true", help="Only core numeric tables for AI")
    parser.add_argument("--from-csv", action="store_true", help="Legacy CSV import instead of API")
    parser.add_argument("--csv-dir", default=str(ROOT / ".csv"))
    args = parser.parse_args()
    db_path = Path(args.db)

    if args.from_csv:
        import_from_csv(db_path, Path(args.csv_dir))
        print("done (csv)")
        return 0

    if not (KOSIS_API_KEY or "").strip():
        print("ERROR: KOSIS_API_KEY not set. Put it in .streamlit/secrets.toml or env.")
        print("Fallback: python make_database.py --from-csv")
        return 2

    if args.core_only:
        result = sync_core_tables(db_path=db_path)
    else:
        result = sync_all(db_path=db_path)
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
