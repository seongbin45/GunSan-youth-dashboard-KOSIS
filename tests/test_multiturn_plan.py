"""Regression from live screenshots: multi-turn must re-plan tools each message."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent
from finfit_youth.tools import execute_tool_dict
from finfit_youth.intent_routing import wants_savings_query


def test_second_stats_question_still_plans_stats_tool():
    """Screenshot bug: turn1 stats → turn2 stats planned 0 steps via trajectory covered."""
    a = FinFitAgent(user_id="mt_stats")
    a.state.first_goal = None

    # Turn 1
    dr1 = a.deep_research("군산시 청년 취업 상황 어때?")
    plan1 = dr1["plan"]
    assert any(
        s["tool"] == "get_gunsan_youth_stats" for s in plan1.get("steps") or []
    ), plan1
    # simulate tool + reflect (as live page does)
    out = execute_tool_dict(
        "get_gunsan_youth_stats", {"category": "employment_difficulty"}
    )
    a.reflect_and_learn(
        "군산시 청년 취업 상황 어때?",
        [{"tool": "get_gunsan_youth_stats", "output": out}],
        "통계 안내",
    )
    assert a.research_trajectory  # after turn1

    # Turn 2 — same-ish stats question must NOT be blocked
    dr2 = a.deep_research("군산시 청년 취업 상황 어때?")
    plan2 = dr2["plan"]
    tools2 = [s["tool"] for s in plan2.get("steps") or []]
    assert tools2 == ["get_gunsan_youth_stats"], (
        f"expected stats tool again, got {tools2}; "
        f"trajectory len after clear={len(a.research_trajectory)}"
    )
    assert plan2.get("clarify") is False
    assert (plan2.get("steps") or [])[0]["args"]["category"] == "employment_difficulty"


def test_deep_research_clears_trajectory():
    a = FinFitAgent(user_id="mt_clear")
    a.research_trajectory = [{"round": 1, "actions": ["get_gunsan_youth_stats"]}]
    a.deep_research("저축 계획만 간단히")
    assert a.research_trajectory == []


def test_money_how_to_save_is_savings_not_clarify():
    """Screenshot: '나 돈 어떻게 모아야할까?' should open savings, not empty clarify."""
    assert wants_savings_query("나 돈 어떻게 모아야할까?") is True
    a = FinFitAgent(user_id="mt_save")
    a.state.first_goal = "비상금"
    a.state.monthly_income = 2_000_000
    a.state.age = 26
    plan = a.deep_research("나 돈 어떻게 모아야할까?")["plan"]
    tools = [s["tool"] for s in plan.get("steps") or []]
    assert "calculate_savings_plan" in tools
    assert plan.get("clarify") is False


def test_profile_income_not_flagged_by_soft_guard():
    a = FinFitAgent(user_id="mt_guard")
    a.clear_turn_scratch()
    a.state.monthly_income = 2_000_000
    a.state.age = 26
    text = a.synthesize_final(
        "당신은 26세, 월 소득 2,000,000원입니다. 충분히 긴 본문으로 soft-check를 통과시킵니다.",
        [],
        "나 돈 어떻게 모아야할까?",
    )
    assert "숫자 검증 경고" not in text
