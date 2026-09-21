"""
One-shot: copy root agent_state_*.json → data/agent_state/ (no delete by default).

Usage (project root):
  python scripts/migrate_agent_state.py
  python scripts/migrate_agent_state.py --delete-legacy   # only after verifying copies
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "agent_state"


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate root agent_state_*.json into data/agent_state/")
    ap.add_argument(
        "--delete-legacy",
        action="store_true",
        help="Delete root copies after successful copy (default: keep both)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only",
    )
    args = ap.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    sources = sorted(ROOT.glob("agent_state_*.json"))
    if not sources:
        print("No root agent_state_*.json found.")
        return 0

    copied = 0
    skipped = 0
    for src in sources:
        dst = DEST / src.name
        if dst.is_file():
            # Prefer newer mtime as destination if already exists
            if src.stat().st_mtime <= dst.stat().st_mtime:
                print(f"SKIP (dest newer/equal): {src.name}")
                skipped += 1
                if args.delete_legacy and not args.dry_run:
                    src.unlink()
                    print(f"  deleted legacy {src.name}")
                continue
        print(f"COPY {src.name} → data/agent_state/")
        if not args.dry_run:
            shutil.copy2(src, dst)
            copied += 1
            if args.delete_legacy:
                src.unlink()
                print(f"  deleted legacy {src.name}")
        else:
            copied += 1

    print(f"Done. copied/planned={copied} skipped={skipped} dest={DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
