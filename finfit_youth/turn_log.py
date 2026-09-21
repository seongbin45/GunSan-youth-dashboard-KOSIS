"""
Offline turn log for manual / scripted cross-checks (no live LLM in CI).

Schema version 1 — one JSON object per line (JSONL):
  schema, ts, user_id, query, mode,
  plan: {tools, categories, clarify, depth},
  tools: [{tool, args_digest, from_db?, category?, n_benefits?, error?}],
  figures_digest: sorted significant numbers from tools,
  assumptions: [{field, value, reason}],
  answer_excerpt, answer_chars,
  guard: {ok, unmatched} | null,
  provider (optional, no keys)

Enable write:
  FINFIT_TURN_LOG=0  → disabled
  FINFIT_TURN_LOG=1  → enabled (default if unset: enabled for local product use)

Never logs API keys, secrets, or full secrets.toml.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = 1
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = _PROJECT_ROOT / "data" / "turn_logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "turns.jsonl"

# Answer body kept short for privacy / size
_ANSWER_EXCERPT_CHARS = 400


def turn_log_enabled() -> bool:
    v = (os.environ.get("FINFIT_TURN_LOG") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _digest_args(args: dict | None) -> str:
    raw = json.dumps(args or {}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _tool_summary(step: dict) -> dict[str, Any]:
    tool = str(step.get("tool") or "")
    if tool.startswith("_"):
        return {"tool": tool, "internal": True}
    out = step.get("output") if isinstance(step.get("output"), dict) else {}
    inp = step.get("input") if isinstance(step.get("input"), dict) else {}
    row: dict[str, Any] = {
        "tool": tool,
        "args_digest": _digest_args(inp),
    }
    if "category" in inp:
        row["category"] = inp.get("category")
    if out.get("category"):
        row["category"] = out.get("category")
    if "from_db" in out:
        row["from_db"] = out.get("from_db")
    if "error" in out:
        row["error"] = str(out.get("error"))[:120]
    if tool == "check_benefit_eligibility":
        row["n_benefits"] = len(out.get("benefits") or [])
    if tool == "calculate_savings_plan":
        for k in ("monthly_savings", "monthly_income", "savings_rate"):
            if k in out:
                row[k] = out.get(k)
    return row


def _figures_digest(tool_results: list | None) -> list[float]:
    try:
        from .answer_guard import extract_allowed_numbers

        nums = extract_allowed_numbers(tool_results)
        return sorted(nums, key=lambda x: (-abs(x), x))[:30]
    except Exception:
        return []


def _strip_secrets(text: str) -> str:
    """Best-effort redact key-like tokens from free text."""
    if not text:
        return text
    # long hex / sk- / AIza style
    text = re.sub(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9]{10,}\b", "[REDACTED]", text)
    text = re.sub(r"\bAIza[A-Za-z0-9_\-]{20,}\b", "[REDACTED]", text)
    return text


def build_turn_record(
    *,
    query: str,
    plan: dict | None = None,
    tool_steps: list | None = None,
    answer: str = "",
    assumptions: list | None = None,
    guard: dict | None = None,
    user_id: str = "default",
    mode: str = "live",
    provider: str | None = None,
    depth: str | None = None,
    extra: dict | None = None,
) -> dict[str, Any]:
    """Build one schema-v1 turn record (pure; no I/O)."""
    plan = plan or {}
    steps = tool_steps or []
    external = [s for s in steps if s.get("tool") and not str(s.get("tool")).startswith("_")]
    plan_tools = [s.get("tool") for s in (plan.get("steps") or []) if s.get("tool")]
    plan_cats = [
        (s.get("args") or {}).get("category")
        for s in (plan.get("steps") or [])
        if s.get("tool") == "get_gunsan_youth_stats"
    ]
    ans = _strip_secrets((answer or "").strip())
    record: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id or "default")[:80],
        "query": _strip_secrets((query or "")[:500]),
        "mode": mode,
        "plan": {
            "tools": plan_tools,
            "categories": plan_cats,
            "clarify": bool(plan.get("clarify")),
            "depth": depth,
        },
        "tools": [_tool_summary(s) for s in steps if s.get("tool")],
        "external_tool_count": len(external),
        "figures_digest": _figures_digest(external),
        "assumptions": [
            {
                "field": a.get("field"),
                "value": a.get("value"),
                "reason": str(a.get("reason") or "")[:160],
            }
            for a in (assumptions or [])
            if isinstance(a, dict)
        ],
        "answer_excerpt": ans[:_ANSWER_EXCERPT_CHARS],
        "answer_chars": len(ans),
        "guard": None,
        "provider": (provider or "")[:40] or None,
    }
    if guard and isinstance(guard, dict):
        record["guard"] = {
            "ok": guard.get("ok"),
            "unmatched": (guard.get("unmatched") or [])[:12],
        }
    if extra:
        # only allow plain JSON-ish extras; drop huge blobs
        safe = {}
        for k, v in list(extra.items())[:12]:
            if k in record:
                continue
            try:
                json.dumps(v, default=str)
                safe[str(k)[:40]] = v
            except Exception:
                safe[str(k)[:40]] = str(v)[:80]
        if safe:
            record["extra"] = safe
    return record


def append_turn_log(
    record: dict[str, Any],
    *,
    path: Path | str | None = None,
    enabled: bool | None = None,
) -> Optional[Path]:
    """
    Append one JSON line. Returns path written, or None if disabled/failed.
    """
    if enabled is None:
        enabled = turn_log_enabled()
    if not enabled:
        return None
    log_path = Path(path) if path else DEFAULT_LOG_FILE
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return log_path
    except Exception:
        return None


def log_agent_turn(
    *,
    query: str,
    plan: dict | None,
    tool_steps: list | None,
    answer: str,
    agent: Any = None,
    mode: str = "live",
    provider: str | None = None,
    path: Path | str | None = None,
    enabled: bool | None = None,
) -> Optional[Path]:
    """Convenience: pull assumptions/guard/user_id from FinFitAgent if given."""
    assumptions = list(getattr(agent, "assumptions", None) or [])
    guard = getattr(agent, "_last_answer_guard", None)
    user_id = getattr(agent, "user_id", "default")
    depth = getattr(agent, "_last_depth", None)
    if depth is None and agent is not None and hasattr(agent, "research_depth"):
        try:
            depth = agent.research_depth(query, plan)
        except Exception:
            depth = None
    rec = build_turn_record(
        query=query,
        plan=plan,
        tool_steps=tool_steps,
        answer=answer,
        assumptions=assumptions,
        guard=guard if isinstance(guard, dict) else None,
        user_id=str(user_id),
        mode=mode,
        provider=provider,
        depth=depth,
    )
    return append_turn_log(rec, path=path, enabled=enabled)
