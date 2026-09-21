"""
API-free demo path — same intent pillars as FinFitAgent.plan / wants_*.

Profile defaults are never silent: each filled default is listed under
「이번 답변에 쓰인 가정」 (parity with agent assumptions).
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional


def run_demo_turn(
    user_message: str,
    *,
    state: Any,
    execute_tool: Callable[[str, dict], str],
    record_assumption: Optional[Callable[[str, Any, str], None]] = None,
) -> tuple[str, list[dict]]:
    """
    Returns (answer_markdown, steps).

    state: object with age, income_level, employment_status, has_house,
           monthly_income, first_goal (UserState-compatible).
    """
    from .intent_routing import (
        wants_benefit_query,
        wants_savings_query,
        wants_stats_query,
        stats_category_for_query,
        is_unclear_intent,
        CLARIFY_INTENT_TEXT,
    )

    steps: list[dict] = []
    parts: list[str] = []
    first_goal = getattr(state, "first_goal", None)
    demo_assumptions: list[dict] = []

    def _assume(field: str, value: Any, reason: str) -> None:
        demo_assumptions.append({"field": field, "value": value, "reason": reason})
        if record_assumption is not None:
            try:
                record_assumption(field, value, f"[데모] {reason}")
            except Exception:
                pass

    need_b = wants_benefit_query(user_message, first_goal)
    need_s = wants_savings_query(user_message)
    need_t = wants_stats_query(user_message)

    if need_b:
        from .income_parse import (
            parse_age_years,
            parse_employment_status,
            parse_has_house,
        )

        parsed_age = parse_age_years(user_message)
        if parsed_age is not None:
            age = int(parsed_age)
            prev = getattr(state, "age", None)
            if prev is not None and int(prev) != age:
                _assume(
                    "age",
                    age,
                    f"이번 질문에 적힌 나이({age}세)를 프로필({int(prev)}세)보다 우선해 조회",
                )
            try:
                state.age = age
            except Exception:
                pass
        elif getattr(state, "age", None) is not None:
            age = state.age
        else:
            age = 25
            _assume("age", age, "나이 미입력 → 혜택 조회용 기본값")
        if getattr(state, "income_level", None):
            income_level = state.income_level
        else:
            income_level = "100%이하"
            _assume("income_level", income_level, "소득수준 미입력 → 중위 100% 이하 가정")
        parsed_emp = parse_employment_status(user_message)
        if parsed_emp is not None:
            employment_status = parsed_emp
            try:
                state.employment_status = employment_status
            except Exception:
                pass
        elif getattr(state, "employment_status", None):
            employment_status = state.employment_status
        else:
            employment_status = "미취업"
            _assume("employment_status", employment_status, "고용상태 미입력 → 미취업 가정")
        parsed_house = parse_has_house(user_message)
        if parsed_house is not None:
            has_house = bool(parsed_house)
            try:
                state.has_house = has_house
            except Exception:
                pass
        elif getattr(state, "has_house", None) is not None:
            has_house = state.has_house
        else:
            has_house = False
            _assume("has_house", has_house, "주택보유 미입력 → 무주택 가정")
        demo_input = {
            "age": age,
            "income_level": income_level,
            "employment_status": employment_status,
            "has_house": has_house,
            "query": (user_message or "")[:80],
        }
        raw = execute_tool("check_benefit_eligibility", demo_input)
        res = json.loads(raw) if isinstance(raw, str) else raw
        steps.append(
            {"tool": "check_benefit_eligibility", "input": demo_input, "output": res}
        )
        parts.append("**✅ 혜택 매칭** (온통청년 캐시 · 신청 확정 아님)")
        parts.append(res.get("summary", "") or "")
        if res.get("disclaimer"):
            parts.append(f"⚠️ {res['disclaimer']}")
        for b in (res.get("benefits") or [])[:5]:
            parts.append(
                f"- **{b.get('name')}** : {b.get('benefit')}\n  조건: {b.get('condition', '')}"
            )

    if need_s:
        from .income_parse import parse_monthly_income_won

        parsed = parse_monthly_income_won(user_message)
        if parsed is not None:
            income = int(parsed)
            prev = getattr(state, "monthly_income", None)
            if prev is not None and int(prev) != income:
                _assume(
                    "monthly_income",
                    income,
                    f"질문 문구 소득({income:,}원)을 프로필({int(prev):,}원)보다 우선",
                )
            else:
                # still honest if profile empty and we took from message — no assume needed
                try:
                    state.monthly_income = income
                except Exception:
                    pass
        elif getattr(state, "monthly_income", None) is not None:
            income = int(state.monthly_income)
        else:
            income = 2300000
            _assume(
                "monthly_income",
                income,
                "월소득 미입력 → 예시 소득으로 저축 계획 계산",
            )
        demo_input = {"income": int(income), "savings_level": 5}
        raw = execute_tool("calculate_savings_plan", demo_input)
        res = json.loads(raw) if isinstance(raw, str) else raw
        steps.append(
            {"tool": "calculate_savings_plan", "input": demo_input, "output": res}
        )
        parts.append(f"\n**💰 저축 계획** (소득 {income:,}원 · 강도 5)")
        parts.append(
            f"- 추천 저축: {res.get('monthly_savings', 0):,}원 ({res.get('savings_rate')})"
        )
        parts.append(
            f"- 고정비: {res.get('monthly_fixed', 0):,}원 / 여가: {res.get('monthly_leisure', 0):,}원"
        )
        if res.get("tip"):
            parts.append(res["tip"])

    if need_t:
        cat = stats_category_for_query(user_message)
        raw = execute_tool("get_gunsan_youth_stats", {"category": cat})
        res = json.loads(raw) if isinstance(raw, str) else raw
        steps.append(
            {
                "tool": "get_gunsan_youth_stats",
                "input": {"category": cat},
                "output": res,
            }
        )
        parts.append(f"\n**📊 통계 `{cat}`** · from_db={res.get('from_db')}")
        parts.append(res.get("data") or res.get("error") or "")
        _m = res.get("metric") or {}
        if _m.get("unit_label_ko") or _m.get("unit_note"):
            parts.append(
                f"  · 단위: {_m.get('unit_label_ko') or _m.get('unit')} "
                f"{('— ' + _m['unit_note']) if _m.get('unit_note') else ''}".rstrip()
            )
        if res.get("insight"):
            parts.append(f"  → {res['insight']}")
        if res.get("disclaimer"):
            parts.append(f"⚠️ {res['disclaimer']}")

    if not parts:
        if is_unclear_intent(user_message, first_goal):
            parts.append("**❓ 데모 모드 · 의도 확인**\n")
            parts.append(CLARIFY_INTENT_TEXT)
            parts.append(
                "\n_(데모는 API 키 없이 동작합니다. 키를 설정하면 LLM이 같은 계획으로 답합니다.)_"
            )
            steps.append(
                {
                    "tool": "_internal_clarify_intent",
                    "input": {"kind": "clarify_intent"},
                    "output": {"clarify_text": CLARIFY_INTENT_TEXT},
                }
            )
        else:
            parts.append(
                "데모에서 실행할 도구가 없었습니다. 혜택 / 저축 / 통계 중 하나를 구체적으로 물어봐 주세요."
            )

    if demo_assumptions:
        assume_lines = [
            "**이번 답변에 쓰인 가정** (데모 · 실제 정보와 다를 수 있음):"
        ]
        for a in demo_assumptions:
            assume_lines.append(f"- {a['field']}: `{a['value']}` — {a['reason']}")
        assume_lines.append(
            "_프로필·가계부를 채우면 가정이 줄고 맞춤도가 올라갑니다._"
        )
        parts = assume_lines + [""] + parts

    return "\n".join(parts), steps
