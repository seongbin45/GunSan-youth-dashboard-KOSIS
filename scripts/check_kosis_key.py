"""Check KOSIS key configuration without printing the full secret."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # project root (scripts/..)
sys.path.insert(0, str(ROOT))


def _scan_file(path: Path) -> list[tuple[str, int, bool, bool]]:
    """Return (key, value_len, is_commented, is_placeholder)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        raw = line
        stripped = line.strip()
        commented = stripped.startswith("#")
        body = stripped[1:].strip() if commented else stripped
        m = re.match(r"([A-Za-z0-9_]*KOSIS[A-Za-z0-9_]*)\s*=\s*(.*)$", body)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip().strip('"').strip("'")
        placeholder = val in (
            "",
            "PASTE_YOUR_KEY_HERE",
            "여기에_발급키",
            "여기에_KOSIS_OpenAPI_인증키_붙여넣기",
        )
        out.append((key, len(val), commented, placeholder, i))
    return out


def main() -> int:
    print("=== FILE SCAN ===")
    for rel in [".streamlit/secrets.toml", ".env", ".env.local"]:
        path = ROOT / rel
        rows = _scan_file(path)
        if not path.is_file():
            print(f"{rel}: missing")
            continue
        if not rows:
            print(f"{rel}: no KOSIS* keys found")
            continue
        for key, n, commented, placeholder, lineno in rows:
            print(
                f"{rel}:{lineno} {key} commented={commented} "
                f"len={n} placeholder={placeholder}"
            )

    print("=== CONFIG LOAD ===")
    from finfit_youth.config import KOSIS_API_KEY, secret_status

    st = secret_status("KOSIS_API_KEY")
    print("configured:", st["configured"])
    print("source:", st["source"])
    print("masked:", st["masked"] or "(none)")
    print("dotenv_files:", st["dotenv_files"])
    print("raw_loaded_len:", len(KOSIS_API_KEY or ""))

    if not st["configured"]:
        print("\nRESULT: KEY NOT LOADED")
        print("Fix: uncomment KOSIS_API_KEY in secrets.toml OR run:")
        print("  python scripts/set_kosis_key.py --key YOUR_KEY --also-env")
        return 1

    print("\n=== LIVE KOSIS SYNC (core tables) ===")
    from finfit_youth.kosis_sync import sync_core_tables
    from finfit_youth.gunsan_stats import get_gunsan_stat

    result = sync_core_tables()
    print("ok:", result.get("ok"))
    print("tables:", result.get("tables"))
    if result.get("errors"):
        print("errors:", result["errors"])

    print("\n=== STATS AFTER SYNC ===")
    for cat in (
        "population",
        "housing",
        "income",
        "employment_difficulty",
        "employment_count",
        "employment",
    ):
        r = get_gunsan_stat(cat)
        print(
            cat,
            "from_db=",
            r.get("from_db"),
            "|",
            (r.get("data") or r.get("error") or "")[:100],
        )

    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
