"""
KOSIS_API_KEY 를 쉽게 설정하는 헬퍼.

Examples (project root에서):
  python scripts/set_kosis_key.py
  python scripts/set_kosis_key.py --key YOUR_KEY
  python scripts/set_kosis_key.py --key YOUR_KEY --also-env
  python scripts/set_kosis_key.py --status
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ROOT / ".streamlit" / "secrets.toml"
SECRETS_EXAMPLE = ROOT / ".streamlit" / "secrets.toml.example"
ENV_PATH = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"


def _upsert_toml_key(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        text = path.read_text(encoding="utf-8-sig")
    elif SECRETS_EXAMPLE.is_file():
        text = SECRETS_EXAMPLE.read_text(encoding="utf-8-sig")
        # strip comment-only placeholder for this key if copying from example
        text = re.sub(
            rf'(?m)^\s*#?\s*{re.escape(key)}\s*=\s*".*"\s*$',
            "",
            text,
        )
    else:
        text = "# Streamlit secrets (auto-created by scripts/set_kosis_key.py)\n"

    # escape backslashes and quotes in value for TOML basic string
    safe = value.replace("\\", "\\\\").replace('"', '\\"')
    line = f'{key} = "{safe}"'
    pattern = re.compile(rf'(?m)^\s*{re.escape(key)}\s*=\s*.*$')
    if pattern.search(text):
        text = pattern.sub(line, text)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n# --- KOSIS (added by set_kosis_key.py) ---\n"
        text += line + "\n"

    path.write_text(text, encoding="utf-8")


def _upsert_env_key(path: Path, key: str, value: str) -> None:
    if path.is_file():
        text = path.read_text(encoding="utf-8-sig")
    elif ENV_EXAMPLE.is_file():
        text = ENV_EXAMPLE.read_text(encoding="utf-8-sig")
    else:
        text = "# local env (auto-created by set_kosis_key.py)\n"

    line = f"{key}={value}"
    pattern = re.compile(rf'(?m)^\s*{re.escape(key)}\s*=\s*.*$')
    if pattern.search(text):
        text = pattern.sub(line, text)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set KOSIS_API_KEY for Streamlit / CLI")
    parser.add_argument("--key", default="", help="API key value (if omitted, prompt)")
    parser.add_argument("--also-env", action="store_true", help="Also write .env for CLI")
    parser.add_argument("--status", action="store_true", help="Show whether key is configured")
    parser.add_argument("--env-only", action="store_true", help="Write only .env (not secrets.toml)")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from finfit_youth.config import secret_status

    if args.status:
        st = secret_status("KOSIS_API_KEY")
        print("KOSIS_API_KEY configured:", st["configured"])
        print("source:", st["source"])
        print("masked:", st["masked"] or "(none)")
        print("dotenv_files:", st["dotenv_files"])
        print("secrets path:", SECRETS)
        print("example:", SECRETS_EXAMPLE)
        return 0 if st["configured"] else 1

    key = (args.key or "").strip()
    if not key:
        print("KOSIS OpenAPI 키를 입력하세요.")
        print("발급: https://kosis.kr/openapi/sw/devInfo/OpenApiRequest.do")
        try:
            key = input("KOSIS_API_KEY> ").strip()
        except EOFError:
            key = ""
    if not key:
        print("ERROR: empty key")
        return 2

    if args.env_only:
        _upsert_env_key(ENV_PATH, "KOSIS_API_KEY", key)
        print(f"Wrote {ENV_PATH}")
    else:
        _upsert_toml_key(SECRETS, "KOSIS_API_KEY", key)
        print(f"Wrote {SECRETS}")
        if args.also_env:
            _upsert_env_key(ENV_PATH, "KOSIS_API_KEY", key)
            print(f"Wrote {ENV_PATH}")

    # re-load for status (new process vars not automatic for toml until streamlit restart)
    print("Done. Streamlit을 재시작하면 secrets가 적용됩니다.")
    print("CLI 확인: python scripts/set_kosis_key.py --status")
    print("동기화:   python KOSIS_Database_Creation_Code/make_database.py --core-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
