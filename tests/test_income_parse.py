"""Message income must win over stale profile for savings tool."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.income_parse import parse_monthly_income_won, parse_age_years
from finfit_youth.agent import FinFitAgent


def test_parse_230_man_won():
    assert parse_monthly_income_won("월급 230만원인데 저축 어떻게 해야 해?") == 2_300_000
    assert parse_monthly_income_won("230만 저축") == 2_300_000
    assert parse_monthly_income_won("소득 2,300,000원") == 2_300_000


def test_parse_none_when_no_amount():
    assert parse_monthly_income_won("저축 계획만 간단히") is None
    assert parse_monthly_income_won("도와줘") is None


def test_parse_age_years():
    assert parse_age_years("나는 28세인데 받을 수 있는 혜택 알려줘") == 28
    assert parse_age_years("만 25세 청년") == 25
    assert parse_age_years("32살 미취업") == 32
    assert parse_age_years("혜택 알려줘") is None
    # out of youth product range
    assert parse_age_years("10세") is None
    assert parse_age_years("50세") is None


def test_savings_args_prefers_message_over_profile():
    """Live log bug: state 2,000,000 overrode stated 230만원."""
    a = FinFitAgent(user_id="inc_parse")
    a.clear_turn_scratch()
    a.state.monthly_income = 2_000_000
    args = a.savings_tool_args(5, "월급 230만원인데 저축 어떻게 해야 해?")
    assert args["income"] == 2_300_000
    assert a.state.monthly_income == 2_300_000


def test_plan_savings_uses_parsed_income():
    a = FinFitAgent(user_id="inc_plan")
    a.clear_turn_scratch()
    a.state.monthly_income = 2_000_000
    a.state.first_goal = None
    plan = a.plan("월급 230만원인데 저축 어떻게 해야 해?")
    steps = [s for s in plan["steps"] if s["tool"] == "calculate_savings_plan"]
    assert len(steps) == 1
    assert steps[0]["args"]["income"] == 2_300_000


def test_benefit_args_prefers_message_age():
    a = FinFitAgent(user_id="age_parse")
    a.clear_turn_scratch()
    a.state.age = 25
    a.state.income_level = "100%이하"
    a.state.employment_status = "미취업"
    a.state.has_house = False
    args = a.benefit_tool_args("나는 28세인데 청년 혜택 알려줘")
    assert args["age"] == 28
    assert a.state.age == 28


def test_plan_benefit_uses_parsed_age():
    a = FinFitAgent(user_id="age_plan")
    a.clear_turn_scratch()
    a.state.age = 25
    a.state.first_goal = None
    plan = a.plan("28살인데 받을 수 있는 청년 혜택 알려줘")
    steps = [s for s in plan["steps"] if s["tool"] == "check_benefit_eligibility"]
    assert len(steps) == 1
    assert steps[0]["args"]["age"] == 28


def test_parse_employment_and_housing():
    from finfit_youth.income_parse import parse_employment_status, parse_has_house

    assert parse_employment_status("나 25살 취준생") == "미취업"
    assert parse_employment_status("직장인인데") == "취업자"
    assert parse_has_house("군산 거주 무주택이야") is False
    assert parse_has_house("유주택자") is True


def test_income_range_ids_and_monthly_to_level():
    from finfit_youth.user_context import (
        income_range_to_income_level,
        monthly_income_to_income_level,
    )

    assert income_range_to_income_level("under50") == "60%이하"
    assert income_range_to_income_level("over200") == "180%이하"
    assert income_range_to_income_level("150to200") == "140%이하"
    assert monthly_income_to_income_level(2_500_000) == "180%이하"
    assert monthly_income_to_income_level(800_000) == "100%이하"


def test_benefit_args_derives_income_level_from_range():
    a = FinFitAgent(user_id="inc_der")
    a.clear_turn_scratch()
    a.state.income_level = None
    a.state.income_range = "over200"
    a.state.age = 25
    a.state.employment_status = "미취업"
    a.state.has_house = False
    args = a.benefit_tool_args("혜택 알려줘")
    assert args["income_level"] == "180%이하"
    assert any(
        x.get("field") == "income_level" and x.get("source") == "derived"
        for x in a.assumptions
    )


def test_benefit_args_parse_chwijun_mujutaek():
    """Live log: 취준생·무주택 must not be labeled '미입력 가정'."""
    a = FinFitAgent(user_id="prof_msg")
    a.clear_turn_scratch()
    a.state.age = None
    a.state.income_level = None
    a.state.employment_status = None
    a.state.has_house = None
    q = "나 25살 취준생, 군산 거주 무주택이야. 받을 수 있는 혜택 다 알려줘."
    args = a.benefit_tool_args(q)
    assert args["age"] == 25
    assert args["employment_status"] == "미취업"
    assert args["has_house"] is False
    # only income_level should remain a true default assumption
    default_fields = {x["field"] for x in a.assumptions if x.get("source") == "default"}
    assert "employment_status" not in default_fields
    assert "has_house" not in default_fields
    assert "age" not in default_fields
    assert "income_level" in default_fields
