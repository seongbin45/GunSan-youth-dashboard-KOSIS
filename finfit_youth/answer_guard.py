"""
Soft numeric grounding for final LLM synthesis.

- Extract allowed numbers from tool outputs (figures / known money fields / data text).
- Build a synthesis block that tells the model not to invent other magnitudes.
- Soft-check final answer text for large unmatched numbers (warn, do not hard-block).

Not a full fact checker — reduces silent invention of KOSIS-scale figures.
"""
from __future__ import annotations

import re
from typing import Any

# Significant magnitudes worth comparing (skip list indices, "1-2 actions", ages-as-small-ints)
_SIGNIFICANT_ABS = 100.0

# Money / rate / figure keys commonly returned by tools
_NUMERIC_KEYS = {
    "monthly_savings",
    "monthly_fixed",
    "monthly_leisure",
    "monthly_income",
    "yearly_savings",
    "gunsan_youth_18_39",
    "youth_15_39_quarterly_mean",
    "all_ages_quarterly_mean",
    "youth_share_pct",
    "youth_ownership_rate_pct",
    "pct",
    "value",
    "DT",
    "rate",
    "share",
}


def _to_float(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "").replace("%", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _walk_numbers(obj: Any, into: set[float], *, depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _NUMERIC_KEYS or isinstance(v, (int, float)):
                fv = _to_float(v)
                if fv is not None:
                    into.add(fv)
            _walk_numbers(v, into, depth=depth + 1)
    elif isinstance(obj, (list, tuple)):
        for x in obj:
            _walk_numbers(x, into, depth=depth + 1)
    else:
        fv = _to_float(obj)
        if fv is not None and abs(fv) >= _SIGNIFICANT_ABS:
            into.add(fv)


_NUM_IN_TEXT = re.compile(
    r"(?<![A-Za-z_])"  # not part of identifier
    r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+)"
    r"(?:\s*%|\s*원|\s*명|\s*세)?"
)


def numbers_from_text(text: str) -> list[float]:
    """Parse numeric tokens from Korean/tool prose."""
    out: list[float] = []
    for m in _NUM_IN_TEXT.finditer(text or ""):
        raw = m.group(1).replace(",", "")
        try:
            out.append(float(raw))
        except ValueError:
            continue
    return out


def extract_allowed_numbers(tool_results: list | None) -> set[float]:
    """Union of significant numbers grounded in external tool outputs."""
    allowed: set[float] = set()
    for r in tool_results or []:
        tool = str(r.get("tool") or "")
        if tool.startswith("_"):
            continue
        out = r.get("output")
        if not isinstance(out, dict):
            continue
        # Full walk: cache_size, scores, URLs in benefits, amounts in free text
        _walk_numbers(out, allowed)
        for k in _NUMERIC_KEYS:
            if k in out:
                fv = _to_float(out.get(k))
                if fv is not None:
                    allowed.add(fv)
        # explicit string scrape (incl. policy ids in urls like WLF00003201 → 3201)
        blob = json_dumps_safe(out)
        for n in numbers_from_text(blob):
            if abs(n) >= _SIGNIFICANT_ABS or is_calendar_year(n):
                allowed.add(n)
    return allowed


def json_dumps_safe(obj: Any) -> str:
    try:
        import json

        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def _approx_in(n: float, allowed: set[float], *, rel: float = 0.02, abs_tol: float = 0.6) -> bool:
    for a in allowed:
        if abs(a - n) <= abs_tol:
            return True
        if a != 0 and abs(a - n) / abs(a) <= rel:
            return True
        # 56,117 vs 56117 already same; also allow 천명-scale half match? no
    return False


def is_calendar_year(n: float) -> bool:
    """
    4-digit calendar years are not KOSIS magnitude claims.
    Live false positive: '청년미래적금(2026신설)' → soft-check warned on 2026.
    """
    if abs(n - round(n)) > 1e-9:
        return False
    y = int(round(n))
    return 1990 <= y <= 2100


def significant_answer_numbers(answer: str) -> list[float]:
    """
    Numbers in the answer that look like data claims (not small counters / years).
    Threshold: abs >= 100; exclude calendar years (policy name years, etc.).
    """
    out = []
    for n in numbers_from_text(answer):
        if abs(n) < _SIGNIFICANT_ABS:
            continue
        if is_calendar_year(n):
            continue
        out.append(n)
    return out


def soft_check_answer(
    answer: str,
    tool_results: list | None,
    *,
    clarify_only: bool = False,
    extra_allowed: set[float] | list[float] | None = None,
) -> dict[str, Any]:
    """
    Soft guard: report unmatched significant numbers.

    clarify_only: no external tools — significant numbers not in extra_allowed
    (e.g. profile income) are suspicious.
    extra_allowed: known profile figures (monthly_income, age-scale skip via threshold).
    Calendar years (1990–2100) are never flagged.
    """
    allowed = extract_allowed_numbers(tool_results)
    if extra_allowed:
        for x in extra_allowed:
            fv = _to_float(x)
            if fv is not None:
                allowed.add(fv)
    # Years appearing in tool source/table names (e.g. 20221231 → also 2022)
    for r in tool_results or []:
        out = r.get("output") if isinstance(r.get("output"), dict) else {}
        for key in ("source", "data", "disclaimer"):
            if isinstance(out.get(key), str):
                for n in numbers_from_text(out[key]):
                    if is_calendar_year(n) or abs(n) >= _SIGNIFICANT_ABS:
                        allowed.add(n)
    claimed = significant_answer_numbers(answer or "")
    unmatched: list[float] = []
    for n in claimed:
        if is_calendar_year(n):
            continue
        if _approx_in(n, allowed):
            continue
        if clarify_only:
            # profile-grounded numbers already in allowed; rest are invents
            unmatched.append(n)
            continue
        if not allowed:
            # tools ran but no parseable figures — only flag very large claims
            if abs(n) >= 1000:
                unmatched.append(n)
            continue
        unmatched.append(n)

    # de-dupe preserving order
    seen: set[float] = set()
    uniq: list[float] = []
    for n in unmatched:
        key = round(n, 4)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(n)

    ok = len(uniq) == 0
    warning = ""
    if not ok:
        sample = ", ".join(f"{n:g}" for n in uniq[:8])
        warning = (
            "⚠️ **숫자 검증 경고**: 답변 속 일부 수치가 이번 도구 결과에 없습니다 "
            f"({sample}). 도구·DB 수치를 우선하세요. (자동 soft-check)"
        )
    return {
        "ok": ok,
        "allowed": sorted(allowed),
        "claimed": claimed,
        "unmatched": uniq,
        "warning_text": warning,
        "clarify_only": clarify_only,
    }


def build_allowed_figures_block(tool_results: list | None) -> str:
    """Text block injected into synthesis context (B1 pre-binding)."""
    allowed = extract_allowed_numbers(tool_results)
    external = [
        r
        for r in (tool_results or [])
        if r.get("tool") and not str(r.get("tool")).startswith("_")
    ]
    if not external:
        return (
            "[ALLOWED FIGURES — none from tools]\n"
            "No external tool numbers this turn. "
            "Do NOT invent population, employment counts, ownership rates, or benefit amounts. "
            "If clarifying intent, avoid any fabricated statistics."
        )
    lines = [
        "[ALLOWED FIGURES — only these magnitudes may be stated as facts]",
        "You may restate, round lightly, or format these. "
        "Do NOT invent other government/KOSIS-scale numbers.",
    ]
    if allowed:
        # show a stable, readable subset
        shown = sorted(allowed, key=lambda x: (-abs(x), x))[:40]
        lines.append("Grounded numbers: " + ", ".join(f"{n:g}" for n in shown))
    else:
        lines.append(
            "Tools ran but no numeric figures were parsed — "
            "prefer qualitative tool text; do not invent magnitudes."
        )
    # short per-tool anchors
    for r in external[:6]:
        tool = r.get("tool")
        out = r.get("output") if isinstance(r.get("output"), dict) else {}
        if tool == "get_gunsan_youth_stats":
            lines.append(
                f"- stats category={out.get('category')}: {(out.get('data') or '')[:160]}"
            )
        elif tool == "calculate_savings_plan":
            lines.append(
                f"- savings: income={out.get('monthly_income')} "
                f"save={out.get('monthly_savings')} rate={out.get('savings_rate')}"
            )
        elif tool == "check_benefit_eligibility":
            n = len(out.get("benefits") or [])
            lines.append(f"- benefits matched: {n} (use names/conditions from tool only)")
    return "\n".join(lines)
