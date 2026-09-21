"""P0-1: needs_more_research is question-scoped tool gaps only — not empty profile."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent


def _agent(uid="refl"):
    a = FinFitAgent(user_id=uid)
    a.clear_turn_scratch()
    a.state.first_goal = None
    a.state.age = None
    a.state.income_level = None
    a.state.monthly_income = None
    return a


def test_benefit_success_without_first_goal_is_sufficient():
    a = _agent("refl_ok")
    tr = [
        {
            "tool": "check_benefit_eligibility",
            "output": {
                "benefits": [
                    {"name": "A"},
                    {"name": "B"},
                    {"name": "C"},
                ]
            },
        }
    ]
    assert a.evaluate_research_sufficiency("받을 수 있는 청년 혜택 알려줘", tr) is False
    r = a.reflect_and_learn("받을 수 있는 청년 혜택 알려줘", tr, "혜택 3개 안내")
    assert r["needs_more_research"] is False
    assert a.state.last_research_was_insufficient is False


def test_empty_benefits_is_insufficient():
    a = _agent("refl_empty")
    tr = [{"tool": "check_benefit_eligibility", "output": {"benefits": []}}]
    assert a.evaluate_research_sufficiency("청년 혜택 알려줘", tr) is True


def test_missing_required_tool_is_insufficient():
    a = _agent("refl_miss")
    assert (
        a.evaluate_research_sufficiency("받을 수 있는 청년 혜택 알려줘", []) is True
    )


def test_savings_ok_without_profile_goal():
    a = _agent("refl_sav")
    tr = [
        {
            "tool": "calculate_savings_plan",
            "output": {
                "monthly_savings": 460000,
                "savings_rate": "20%",
                "monthly_income": 2300000,
            },
        }
    ]
    assert a.evaluate_research_sufficiency("저축 계획만 간단히", tr) is False


def test_stats_error_is_insufficient():
    a = _agent("refl_st")
    tr = [{"tool": "get_gunsan_youth_stats", "output": {"error": "db missing"}}]
    assert a.evaluate_research_sufficiency("군산시 청년 인구 현황 어때?", tr) is True


def test_unclear_intent_never_needs_more_tools():
    a = _agent("refl_cl")
    assert a.evaluate_research_sufficiency("도와줘", []) is False
