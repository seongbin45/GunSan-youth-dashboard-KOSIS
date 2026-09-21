"""Grounded answers must restate tool data only (no invented benefits/stats)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.grounded_answer import (
    try_grounded_answer,
    classify_grounding_mode,
    plan_external_tools_complete,
)
from finfit_youth.tools import execute_tool_dict


def test_stats_only_skips_llm_and_contains_db_figures():
    out = execute_tool_dict(
        "get_gunsan_youth_stats", {"category": "employment_difficulty"}
    )
    steps = [
        {
            "tool": "get_gunsan_youth_stats",
            "input": {"category": "employment_difficulty"},
            "output": out,
        }
    ]
    assert classify_grounding_mode(steps) == "stats_only"
    g = try_grounded_answer("군산시 청년 취업 상황 어때?", steps)
    assert g["skip_llm"] is True
    assert g["answer"]
    text = g["answer"]
    assert "33.7" in text or "33.7%" in text
    assert "출처" in text or "source" in text.lower() or "gunsan" in text.lower()
    # must not invent benefit-open advice as core product of stats template
    assert "청년도약계좌를 개설" not in text
    assert "LLM" in text or "근거 고정" in text or "통계" in text


def test_stats_answer_does_not_list_random_benefits():
    out = execute_tool_dict(
        "get_gunsan_youth_stats", {"category": "employment_difficulty"}
    )
    steps = [
        {
            "tool": "get_gunsan_youth_stats",
            "input": {"category": "employment_difficulty"},
            "output": out,
        }
    ]
    g = try_grounded_answer("군산시 청년 취업 상황 어때?", steps)
    # known problematic digression from live log
    assert "국민취업지원제도" not in (g["answer"] or "")
    assert "전세보증금" not in (g["answer"] or "")


def test_savings_only_grounded():
    out = execute_tool_dict(
        "calculate_savings_plan", {"income": 2000000, "savings_level": 5}
    )
    steps = [
        {
            "tool": "calculate_savings_plan",
            "input": {"income": 2000000, "savings_level": 5},
            "output": out,
        }
    ]
    assert classify_grounding_mode(steps) == "savings_only"
    g = try_grounded_answer("저축 계획만 간단히", steps)
    assert g["skip_llm"] is True
    assert "2,000,000" in g["answer"] or "2000000" in g["answer"].replace(",", "")
    assert str(out.get("monthly_savings")) in g["answer"].replace(",", "") or (
        f"{out.get('monthly_savings'):,}" in g["answer"]
    )


def test_multi_tool_concat_skips_llm():
    steps = [
        {
            "tool": "check_benefit_eligibility",
            "output": {
                "benefits": [{"name": "테스트혜택A", "benefit": "지원금", "condition": "19-39"}],
                "summary": "1건",
                "disclaimer": "확정 아님",
            },
        },
        {
            "tool": "get_gunsan_youth_stats",
            "output": {
                "data": "인구 예시 56117",
                "category": "population",
                "from_db": True,
                "source": "db",
                "figures": {"gunsan_youth_18_39": 56117},
            },
        },
    ]
    assert classify_grounding_mode(steps) == "multi"
    g = try_grounded_answer("혜택이랑 현황", steps)
    assert g["skip_llm"] is True
    assert g["reason"] == "multi_pillar_concat_template"
    text = g["answer"] or ""
    assert "테스트혜택A" in text
    assert "56117" in text
    assert "---" in text  # section separator
    # single combined footer — not 2× "다음에 할 수 있는 것"
    assert text.count("다음에 할 수 있는 것") <= 1
    assert "종합 안내" in text


def test_plan_tools_complete_helper():
    plan = {
        "steps": [
            {"tool": "calculate_savings_plan", "args": {"income": 2500000}},
        ]
    }
    assert plan_external_tools_complete(plan, []) is False
    assert (
        plan_external_tools_complete(
            plan,
            [{"tool": "calculate_savings_plan", "output": {"monthly_savings": 1}}],
        )
        is True
    )
    assert plan_external_tools_complete({"steps": [], "clarify": True}, []) is True


def test_no_tools_clarify_fixed():
    assert classify_grounding_mode([]) == "none"
    g = try_grounded_answer(
        "도와줘",
        [],
        plan={"clarify": True, "clarify_text": "질문이 여러 방향으로"},
    )
    assert g["skip_llm"] is True
    assert g["mode"] == "clarify"
    assert "의도" in (g["answer"] or "") or "질문" in (g["answer"] or "")


def test_benefit_only_skips_llm_and_uses_tool_names():
    out = execute_tool_dict(
        "check_benefit_eligibility",
        {
            "age": 25,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "query": "청년",
        },
    )
    steps = [
        {
            "tool": "check_benefit_eligibility",
            "input": {
                "age": 25,
                "income_level": "100%이하",
                "employment_status": "미취업",
                "has_house": False,
                "query": "청년",
            },
            "output": out,
        }
    ]
    assert classify_grounding_mode(steps) == "benefit_only"
    g = try_grounded_answer("받을 수 있는 청년 혜택 알려줘", steps)
    assert g["skip_llm"] is True
    assert g["reason"] == "benefit_only_tool_template"
    text = g["answer"] or ""
    assert "혜택 매칭" in text or "추천" in text
    # first tool benefit name should appear if any matched
    bens = out.get("benefits") or []
    if bens:
        assert bens[0].get("name") in text
    # honesty: not application confirmation
    assert "확정" in text or "disclaimer" in text.lower() or "공고" in text
    # must not invent stats magnitudes
    assert "33.7" not in text


def test_benefit_template_does_not_invent_employment_stats():
    """Even if profile talks employment, benefit-only answer stays on match list."""
    out = execute_tool_dict(
        "check_benefit_eligibility",
        {
            "age": 26,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "query": "취업",
        },
    )
    steps = [{"tool": "check_benefit_eligibility", "output": out}]
    g = try_grounded_answer("취업 지원 혜택", steps)
    assert g["skip_llm"] is True
    assert "employment_difficulty" not in (g["answer"] or "")
    assert "사회조사" not in (g["answer"] or "")
