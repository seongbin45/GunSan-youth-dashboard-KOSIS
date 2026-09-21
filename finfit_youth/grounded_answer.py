"""
Deterministic user-facing answers grounded only in tool outputs.

Accuracy-first:
- stats-only → skip LLM; template from get_gunsan_youth_stats
- savings-only → skip LLM; template from calculate_savings_plan
- benefit-only → skip LLM; template from check_benefit_eligibility

Multi-tool / none / error → skip_llm=False (caller may use LLM or clarify).
Never invents facts; only restates tool fields.
"""
from __future__ import annotations

from typing import Any


def _external_steps(tool_results: list | None) -> list[dict]:
    out = []
    for r in tool_results or []:
        t = str(r.get("tool") or "")
        if not t or t.startswith("_"):
            continue
        out.append(r)
    return out


def _out(step: dict) -> dict:
    o = step.get("output")
    return o if isinstance(o, dict) else {}


def classify_grounding_mode(tool_results: list | None) -> str:
    """
    Returns one of:
      stats_only | savings_only | benefit_only | multi | none | error
    """
    ext = _external_steps(tool_results)
    if not ext:
        return "none"
    tools = [str(s.get("tool")) for s in ext]
    # any hard error with no usable body
    for s in ext:
        o = _out(s)
        if o.get("error") and not (o.get("data") or o.get("benefits") or o.get("monthly_savings") is not None):
            return "error"
    uniq = set(tools)
    if uniq == {"get_gunsan_youth_stats"}:
        return "stats_only"
    if uniq == {"calculate_savings_plan"}:
        return "savings_only"
    if uniq == {"check_benefit_eligibility"}:
        return "benefit_only"
    return "multi"


def _format_stats_answer(step: dict) -> str:
    o = _out(step)
    if o.get("error"):
        return (
            "통계 조회 중 오류가 있었습니다.\n\n"
            f"- 오류: {o.get('error')}\n"
            "페이지 **군산시 청년 데이터** 또는 DB 동기화 상태를 확인해 주세요."
        )
    lines: list[str] = []
    cat = o.get("category") or (step.get("input") or {}).get("category") or "통계"
    lines.append(f"### 군산·전북 청년 통계 (`{cat}`)")
    if o.get("data"):
        lines.append(str(o["data"]))
    if o.get("insight"):
        lines.append(f"\n**해석 참고:** {o['insight']}")
    # optional top figures for employment_difficulty
    figs = o.get("figures") or {}
    top = figs.get("difficulty_top") or []
    if top and isinstance(top, list):
        lines.append("\n**상위 요인 (DB):**")
        for i, row in enumerate(top[:5], 1):
            if not isinstance(row, dict):
                continue
            reason = row.get("reason") or ""
            pct = row.get("pct")
            if pct is not None:
                lines.append(f"{i}. {reason} — **{pct}%**")
            else:
                lines.append(f"{i}. {reason}")
    # population etc.
    if figs.get("gunsan_youth_18_39") is not None and "difficulty" not in str(cat):
        lines.append(f"\n- 군산 청년(18~39) 인구: **{figs['gunsan_youth_18_39']:,}**")
    if figs.get("youth_15_39_quarterly_mean") is not None:
        lines.append(
            f"\n- 전북 15~39 취업자 분기평균: **{figs['youth_15_39_quarterly_mean']}** "
            f"(단위는 원표 기준 · 군산 단독 아님)"
        )
    if o.get("source"):
        lines.append(f"\n**출처:** {o['source']}")
    metric = o.get("metric") or {}
    if metric.get("geography") or metric.get("unit"):
        u = metric.get("unit_label_ko") or metric.get("unit") or ""
        lines.append(
            f"**지표 정의:** 지역={metric.get('geography') or '-'} · 단위={u}"
        )
    if o.get("from_db") is True:
        lines.append("**from_db:** 예 (로컬 DB 값)")
    elif o.get("from_db") is False:
        lines.append("**from_db:** 아니오 (폴백·오류 가능)")
    if o.get("disclaimer"):
        lines.append(f"\n⚠️ {o['disclaimer']}")
    lines.append(
        "\n**다음에 할 수 있는 것**\n"
        "1. 같은 주제로 다른 지표를 물어보기 "
        "(예: 전북 취업자 수, 인구 현황, 주택 소유율)\n"
        "2. 혜택·저축이 필요하면 그 의도를 **따로** 질문하기 "
        "(이 답은 통계 도구 결과만 담고 있습니다)"
    )
    return "\n".join(lines)


def _format_savings_answer(step: dict) -> str:
    o = _out(step)
    if o.get("error"):
        return f"저축 계획 계산 오류: {o.get('error')}"
    inc = o.get("monthly_income")
    save = o.get("monthly_savings")
    rate = o.get("savings_rate")
    fixed = o.get("monthly_fixed")
    leisure = o.get("monthly_leisure")
    yearly = o.get("yearly_savings")
    lines = [
        "### 저축·예산 계획 (계산 도구 결과)",
        f"- 월 소득: **{inc:,}원**" if isinstance(inc, (int, float)) else f"- 월 소득: {inc}",
        f"- 추천 저축: **{save:,}원** ({rate})"
        if isinstance(save, (int, float))
        else f"- 추천 저축: {save} ({rate})",
    ]
    if isinstance(fixed, (int, float)):
        lines.append(f"- 고정비 배분: **{fixed:,}원**")
    if isinstance(leisure, (int, float)):
        lines.append(f"- 여가·식비 배분: **{leisure:,}원**")
    if isinstance(yearly, (int, float)):
        lines.append(f"- 연간 저축 환산: **{yearly:,}원**")
    if o.get("level_name"):
        lines.append(f"- 저축 강도 단계: {o['level_name']}")
    if o.get("tip"):
        lines.append(f"\n{o['tip']}")
    lines.append(
        "\n**참고:** 위 숫자는 `calculate_savings_plan` 도구 출력입니다. "
        "정부 지원 상품 자격은 이 계산에 포함되지 않습니다. "
        "혜택이 필요하면 혜택 질문을 따로 해 주세요."
    )
    return "\n".join(lines)


def _format_benefit_answer(step: dict, *, limit: int = 8) -> str:
    """Restate match_benefits / check_benefit_eligibility output only."""
    o = _out(step)
    if o.get("error"):
        return f"혜택 매칭 오류: {o.get('error')}"

    lines: list[str] = ["### 청년 혜택 매칭 (도구 결과)"]
    if o.get("summary"):
        lines.append(str(o["summary"]))
    # profile used for this match
    prof = o.get("profile_used") or {}
    if prof:
        bits = []
        if prof.get("age") is not None:
            bits.append(f"나이 {prof['age']}")
        if prof.get("income_level"):
            bits.append(f"소득 {prof['income_level']}")
        if prof.get("employment_status"):
            bits.append(f"고용 {prof['employment_status']}")
        if "has_house" in prof:
            bits.append("주택 " + ("있음" if prof.get("has_house") else "무주택"))
        if bits:
            lines.append("**조회에 쓴 조건:** " + " · ".join(bits))
    if o.get("query"):
        lines.append(f"**검색 가중 키워드:** {o['query']}")

    benefits = o.get("benefits") or []
    n = len(benefits)
    shown = benefits[: max(1, min(limit, 12))]
    if not shown:
        lines.append(
            "\n조건에 맞는 정책을 캐시에서 찾지 못했습니다. "
            "페이지 **청년혜택업데이트**에서 동기화했는지, 조건을 바꿔 다시 물어봐 주세요."
        )
    else:
        lines.append(f"\n**추천 목록 (상위 {len(shown)} / 전체 매칭 {n}건):**")
        for i, b in enumerate(shown, 1):
            if not isinstance(b, dict):
                continue
            name = b.get("name") or "(이름 없음)"
            cat = b.get("category") or ""
            benefit = (b.get("benefit") or "").strip().replace("\n", " ")
            if len(benefit) > 180:
                benefit = benefit[:177] + "…"
            cond = b.get("condition") or ""
            region = b.get("region_match") or ""
            lines.append(f"\n**{i}. {name}**" + (f" · {cat}" if cat else ""))
            if benefit:
                lines.append(f"  - 지원: {benefit}")
            if cond:
                lines.append(f"  - 조건: {cond}")
            if region:
                lines.append(f"  - 지역 매칭: {region}")
            if b.get("url"):
                lines.append(f"  - 링크: {b['url']}")
            # score is tool-internal; show lightly for transparency
            if b.get("score") is not None:
                lines.append(f"  - 매칭 점수(휴리스틱): {b['score']}")

    # honesty fields from enrich_benefits_result
    if o.get("data_source"):
        lines.append(f"\n**데이터 출처:** {o['data_source']}")
    if o.get("cache_size") is not None:
        age = o.get("cache_age_text") or (
            f"{o.get('cache_age_seconds')}초" if o.get("cache_age_seconds") is not None else "-"
        )
        lines.append(f"**캐시:** {int(o['cache_size']):,}건 · 갱신 {age}")
    if o.get("method"):
        lines.append(f"**방법:** {o['method']}")
    if o.get("is_fallback"):
        lines.append(
            "⚠️ **폴백 목록**이 포함되었을 수 있습니다. "
            "7_청년혜택업데이트에서 정책을 동기화하세요."
        )
    if o.get("disclaimer"):
        lines.append(f"\n⚠️ {o['disclaimer']}")
    elif o.get("limitations"):
        lines.append("\n**한계:** " + " · ".join(str(x) for x in (o.get("limitations") or [])[:3]))

    lines.append(
        "\n**다음에 할 수 있는 것**\n"
        "1. 관심 정책 이름으로 공식 공고·신청 페이지를 확인하기\n"
        "2. 나이·소득·고용 조건을 바꾼 뒤 다시 매칭 요청하기\n"
        "3. 저축·지역 통계가 필요하면 **따로** 질문하기 "
        "(이 답은 혜택 매칭 도구 결과만 담고 있습니다)"
    )
    return "\n".join(lines)


def _pick_step(ext: list[dict], tool_name: str) -> dict | None:
    chosen = None
    for s in ext:
        if str(s.get("tool")) != tool_name:
            continue
        chosen = s
        o = _out(s)
        # prefer steps with real payload
        if tool_name == "get_gunsan_youth_stats" and (o.get("data") or o.get("figures")):
            return s
        if tool_name == "check_benefit_eligibility" and (
            o.get("benefits") is not None or o.get("summary")
        ):
            return s
        if tool_name == "calculate_savings_plan" and (
            o.get("monthly_savings") is not None or o.get("error")
        ):
            return s
    return chosen


def _strip_next_actions_block(text: str) -> str:
    """Remove per-section '다음에 할 수 있는 것' when concatenating multi (one footer only)."""
    marker = "\n**다음에 할 수 있는 것**"
    if marker in (text or ""):
        return (text or "").split(marker)[0].rstrip()
    return text or ""


def plan_external_tools_complete(plan: dict | None, tool_results: list | None) -> bool:
    """
    True when every non-internal tool in plan.steps has at least one external result.
    Empty plan (clarify) → True (no tools required).
    """
    plan = plan or {}
    planned = [
        str(s.get("tool"))
        for s in (plan.get("steps") or [])
        if s.get("tool") and not str(s.get("tool")).startswith("_")
    ]
    if not planned:
        return True
    done = {
        str(r.get("tool"))
        for r in (tool_results or [])
        if r.get("tool") and not str(r.get("tool")).startswith("_")
    }
    return all(t in done for t in planned)


def _format_multi_answer(ext: list[dict]) -> str:
    """Concatenate per-pillar templates in stable order (benefit → savings → stats)."""
    order = [
        ("check_benefit_eligibility", "benefit", lambda s: _format_benefit_answer(s, limit=5)),
        ("calculate_savings_plan", "savings", _format_savings_answer),
        ("get_gunsan_youth_stats", "stats", _format_stats_answer),
    ]
    parts: list[str] = [
        "아래는 **이번 턴에 실행된 도구 결과**를 축별로 붙인 것입니다. "
        "도구에 없는 사실·수치는 추가하지 않았습니다."
    ]
    used = []
    for tool_name, label, fmt in order:
        step = _pick_step(ext, tool_name)
        if not step:
            continue
        used.append(label)
        parts.append(_strip_next_actions_block(fmt(step)))
    # unknown tools (should be rare)
    known = {t for t, _, _ in order}
    for s in ext:
        t = str(s.get("tool") or "")
        if t and t not in known:
            parts.append(f"### 기타 도구 `{t}`\n```\n{str(_out(s))[:800]}\n```")
            used.append(t)
    parts.append(
        "**종합 안내**\n"
        f"- 포함된 축: {', '.join(used) if used else '(없음)'}\n"
        "- 각 섹션의 수치·목록은 해당 도구 출력과 동일합니다.\n"
        "- 더 깊게 보려면 한 축만 골라 다시 질문해 주세요."
    )
    return "\n\n---\n\n".join(parts)


def try_grounded_answer(
    user_message: str,
    tool_results: list | None,
    *,
    state: Any = None,
    plan: dict | None = None,
) -> dict[str, Any]:
    """
    Build a grounded answer when tools (or clarify) fully determine the reply.

    Returns:
      {
        mode: str,
        skip_llm: bool,
        answer: str | None,
        reason: str,
      }
    """
    mode = classify_grounding_mode(tool_results)
    ext = _external_steps(tool_results)
    plan = plan or {}
    first_goal = getattr(state, "first_goal", None) if state is not None else None

    if mode == "stats_only":
        step = _pick_step(ext, "get_gunsan_youth_stats") or ext[-1]
        return {
            "mode": mode,
            "skip_llm": True,
            "answer": _format_stats_answer(step),
            "reason": "stats_only_tool_template",
        }

    if mode == "savings_only":
        step = _pick_step(ext, "calculate_savings_plan") or ext[-1]
        return {
            "mode": mode,
            "skip_llm": True,
            "answer": _format_savings_answer(step),
            "reason": "savings_only_tool_template",
        }

    if mode == "benefit_only":
        step = _pick_step(ext, "check_benefit_eligibility") or ext[-1]
        return {
            "mode": mode,
            "skip_llm": True,
            "answer": _format_benefit_answer(step),
            "reason": "benefit_only_tool_template",
        }

    if mode == "multi":
        return {
            "mode": mode,
            "skip_llm": True,
            "answer": _format_multi_answer(ext),
            "reason": "multi_pillar_concat_template",
        }

    # no external tools: fixed clarify (no LLM invention)
    if mode == "none":
        from .intent_routing import is_unclear_intent, CLARIFY_INTENT_TEXT

        if plan.get("clarify") or is_unclear_intent(user_message, first_goal):
            text = plan.get("clarify_text") or CLARIFY_INTENT_TEXT
            return {
                "mode": "clarify",
                "skip_llm": True,
                "answer": (
                    "### 의도 확인\n\n"
                    + text
                    + "\n\n_(도구를 실행하지 않았습니다. 위 중 하나를 골라 주시면 "
                    "해당 도구만 조회합니다.)_"
                ),
                "reason": "clarify_fixed_template",
            }

    if mode == "error":
        # surface tool errors without LLM
        bits = []
        for s in ext:
            o = _out(s)
            if o.get("error"):
                bits.append(f"- `{s.get('tool')}`: {o.get('error')}")
        return {
            "mode": mode,
            "skip_llm": True,
            "answer": "도구 실행 오류가 있었습니다.\n\n" + ("\n".join(bits) or str(ext)),
            "reason": "tool_error_template",
        }

    return {
        "mode": mode,
        "skip_llm": False,
        "answer": None,
        "reason": f"mode_{mode}_use_llm_or_caller",
    }


def grounded_preamble_for_ui(grounded: dict[str, Any]) -> str:
    """Short honesty line when we skipped LLM."""
    if not grounded or not grounded.get("skip_llm"):
        return ""
    mode = grounded.get("mode")
    if mode == "stats_only":
        return (
            "🔒 **근거 고정 답변** — 통계 도구 결과만 사용했습니다. "
            "LLM이 수치를 다시 쓰지 않습니다."
        )
    if mode == "savings_only":
        return (
            "🔒 **근거 고정 답변** — 저축 계산 도구 결과만 사용했습니다. "
            "LLM이 수치를 다시 쓰지 않습니다."
        )
    if mode == "benefit_only":
        return (
            "🔒 **근거 고정 답변** — 혜택 매칭 도구 결과만 사용했습니다. "
            "LLM이 자격을 확정·재작성하지 않습니다. (신청 확정 아님)"
        )
    if mode == "multi":
        return (
            "🔒 **근거 고정 답변** — 실행된 도구 결과를 축별로 이어 붙였습니다. "
            "LLM이 축 사이를 섞어 새 사실을 만들지 않습니다."
        )
    if mode == "clarify":
        return (
            "🔒 **근거 고정 답변** — 의도 확인 안내입니다. "
            "도구·통계·혜택을 추정하지 않았습니다."
        )
    if mode == "error":
        return "⚠️ **도구 오류** — 오류 메시지만 표시합니다."
    return ""
