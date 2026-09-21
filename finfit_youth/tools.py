"""
FinFit AI tool registry + execution.

Single place for:
- tool JSON schemas used by LLM providers
- pure Python implementations (benefits / stats / savings)

Streamlit AI page should only import execute_tool / BASE_TOOLS — not reimplement.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from .config import LEVELS


# --- implementations ---

def tool_check_benefit(
    age: int,
    income_level: str,
    employment_status: str,
    has_house: bool,
    query: str = "",
) -> dict[str, Any]:
    """온통청년 정책 캐시 매칭 (benefits_matcher)."""
    from .benefits_matcher import match_benefits

    return match_benefits(
        age=int(age),
        income_level=str(income_level or ""),
        employment_status=str(employment_status or ""),
        has_house=bool(has_house),
        query=str(query or ""),
        limit=12,
    )


def tool_gunsan_stats(category: str) -> dict[str, Any]:
    """군산 통계 — page 6 / Main 과 동일 gunsan_stats."""
    from .gunsan_stats import get_gunsan_stat

    return get_gunsan_stat(category)


def tool_savings_plan(income: int, savings_level: int) -> dict[str, Any]:
    """LEVELS 기반 예산/저축 계획."""
    try:
        level = int(savings_level)
        inc = int(income)
    except Exception:
        return {"error": "income과 savings_level은 정수여야 합니다"}
    if not (1 <= level <= 10):
        return {"error": "savings_level은 1~10 사이여야 합니다"}
    if level not in LEVELS:
        return {"error": f"알 수 없는 savings_level: {level}"}
    lv = LEVELS[level]
    save = int(inc * lv["save"])
    return {
        "level_name": lv["name"],
        "monthly_income": inc,
        "monthly_savings": save,
        "monthly_fixed": int(inc * lv["fix"]),
        "monthly_leisure": int(inc * lv["leisure"]),
        "yearly_savings": save * 12,
        "savings_rate": f"{int(lv['save'] * 100)}%",
        "tip": (
            f"1년 후 예상 저축액 {save * 12:,}원. "
            "청년도약계좌 연동 시 정부기여금 추가 수령 가능."
        ),
    }


TOOL_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "check_benefit_eligibility": tool_check_benefit,
    "get_gunsan_youth_stats": tool_gunsan_stats,
    "calculate_savings_plan": tool_savings_plan,
}

# LLM-facing schemas (provider adapters map these to Anthropic/OpenAI/Google)
BASE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_benefit_eligibility",
        "description": (
            "온통청년 정책 캐시(YouthDataService/7_청년혜택업데이트 동기화)에서 "
            "사용자 나이·소득·고용·주택 조건과 지역(군산·전북 가점)으로 청년 정책을 매칭합니다. "
            "혜택/지원/적금/대출/자격 질문에 우선 호출. 선택 query로 검색어 가중 가능."
        ),
        "properties": {
            "age": {"type": "integer", "description": "만 나이 (예: 25)"},
            "income_level": {
                "type": "string",
                "description": "중위소득 기준",
                "enum": ["60%이하", "100%이하", "140%이하", "150%이하", "180%이하", "소득기준초과"],
            },
            "employment_status": {
                "type": "string",
                "description": "고용 상태",
                "enum": ["미취업", "취업자", "창업자", "농업종사자"],
            },
            "has_house": {
                "type": "boolean",
                "description": "주택 소유 여부 (true=있음, false=무주택)",
            },
            "query": {
                "type": "string",
                "description": "검색 가중 키워드 (예: 월세, 취업, 적금)",
            },
        },
        "required": ["age", "income_level", "employment_status", "has_house"],
    },
    {
        "name": "get_gunsan_youth_stats",
        "description": (
            "로컬 gunsan_youth_data.db(6페이지·Main과 동일)에서 통계 조회. "
            "category: population|housing|income|"
            "employment(묶음)|employment_difficulty(군산 어려움%)|"
            "employment_count(전북 취업자 분기평균). "
            "취업 질문: 어려움→employment_difficulty, 취업자 수→employment_count, "
            "둘 다 필요 시에만 employment."
        ),
        "properties": {
            "category": {
                "type": "string",
                "description": "조회 카테고리 (취업 지표는 단위·지역이 다름 — 분리 카테고리 권장)",
                "enum": [
                    "population",
                    "employment",
                    "employment_difficulty",
                    "employment_count",
                    "housing",
                    "income",
                ],
            }
        },
        "required": ["category"],
    },
    {
        "name": "calculate_savings_plan",
        "description": (
            "월 소득과 저축 강도(1~10)로 현실적인 예산/저축 계획 계산. "
            "'저축', '예산', '생활비', '얼마 모아야', '계획 세워줘' 질문에 사용. "
            "savings_level은 1(여가 많음) ~ 10(극단 절약)."
        ),
        "properties": {
            "income": {
                "type": "integer",
                "description": "월 소득 (원 단위, 예: 2300000)",
            },
            "savings_level": {
                "type": "integer",
                "description": "저축 강도 (1~10)",
            },
        },
        "required": ["income", "savings_level"],
    },
]

TOOL_LABELS: dict[str, str] = {
    "check_benefit_eligibility": "🔍 혜택 자격 확인",
    "get_gunsan_youth_stats": "📊 군산 통계 조회",
    "calculate_savings_plan": "💰 저축 계획 계산",
}


def execute_tool(name: str, inputs: dict | None = None) -> str:
    """
    Run a named tool; always return a JSON string (for LLM tool-result messages).
    """
    inputs = inputs or {}
    fn = TOOL_HANDLERS.get(name)
    if fn is None:
        return json.dumps({"error": f"알 수 없는 tool: {name}"}, ensure_ascii=False)
    try:
        result = fn(**inputs)
    except TypeError as e:
        result = {"error": str(e)}
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(result, ensure_ascii=False)


def execute_tool_dict(name: str, inputs: dict | None = None) -> dict[str, Any]:
    """Same as execute_tool but returns a dict (for tests / agent ingest)."""
    raw = execute_tool(name, inputs)
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else {"raw": out}
    except Exception:
        return {"error": "invalid tool json", "raw": raw}
