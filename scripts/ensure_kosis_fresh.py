"""
KOSIS 핵심 표 TTL 검사 및 필요 시만 갱신 (네트워크는 stale일 때만).

Examples (project root):
  python scripts/ensure_kosis_fresh.py --status
  python scripts/ensure_kosis_fresh.py
  python scripts/ensure_kosis_fresh.py --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Ensure KOSIS core tables are within TTL")
    ap.add_argument(
        "--status",
        action="store_true",
        help="Print freshness only (no network)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Force sync_core_tables even if within TTL (requires API key)",
    )
    ap.add_argument(
        "--ttl",
        type=int,
        default=None,
        help="Override TTL seconds (default: GUNSAN_STATS_SYNC_TTL_SECONDS)",
    )
    args = ap.parse_args()

    from finfit_youth.kosis_sync import (
        core_freshness_status,
        ensure_fresh_core,
        sync_core_tables,
    )
    from finfit_youth.config import secret_status

    st = core_freshness_status(ttl=args.ttl)
    print("=== KOSIS CORE FRESHNESS ===")
    print("db:", st["db_path"])
    print("db_exists:", st["db_exists"])
    print("stale:", st["stale"])
    print("age:", st["age_text"], f"({st['age_seconds']})")
    print("ttl_days:", st["ttl_days"], f"({st['ttl_seconds']}s)")
    print("summary:", st["summary"])

    ks = secret_status("KOSIS_API_KEY")
    print("key_configured:", ks.get("configured"), "source:", ks.get("source"))

    if args.status:
        return 0 if not st["stale"] else 2

    if args.force:
        if not ks.get("configured"):
            print("ERROR: KOSIS_API_KEY not configured; cannot force sync")
            return 1
        print("=== FORCE sync_core_tables ===")
        result = sync_core_tables()
        print("ok:", result.get("ok"))
        print("tables:", result.get("tables"))
        if result.get("errors"):
            print("errors:", result["errors"])
            return 1
        return 0

    print("=== ensure_fresh_core ===")
    result = ensure_fresh_core(ttl=args.ttl)
    print("result:", {k: result.get(k) for k in ("ok", "skipped", "reason", "error", "age_seconds")})
    if result.get("tables"):
        print("tables:", result.get("tables"))
    if result.get("errors"):
        print("errors:", result["errors"])
        return 1
    if result.get("skipped") and result.get("reason") == "KOSIS_API_KEY not set" and st["stale"]:
        return 1
    return 0 if result.get("ok") or result.get("skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
