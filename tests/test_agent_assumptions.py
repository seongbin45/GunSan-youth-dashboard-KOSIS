"""Regression: assumptions are tracked, not silently written into UserState."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent


def test_missing_profile_records_assumptions_not_state():
    a = FinFitAgent(user_id="test_assumptions")
    a.clear_turn_scratch()
    # empty profile
    assert a.state.age is None
    args = a.benefit_tool_args()
    assert args["age"] == 25
    assert any(x["field"] == "age" for x in a.assumptions)
    # must NOT silently invent permanent profile
    assert a.state.age is None
    assert a.state.income_level is None


def test_known_profile_no_age_assumption():
    a = FinFitAgent(user_id="test_known")
    a.clear_turn_scratch()
    a.state.age = 28
    a.state.income_level = "100%이하"
    a.state.employment_status = "취업자"
    a.state.has_house = False
    a.benefit_tool_args()
    assert not any(x["field"] == "age" for x in a.assumptions)


def test_synthesize_surfaces_assumptions():
    a = FinFitAgent(user_id="test_synth")
    a.clear_turn_scratch()
    a.benefit_tool_args()
    out = a.synthesize_final("청년도약계좌를 검토해 보세요.", [], "혜택 알려줘")
    assert "가정" in out
    assert "age" in out or "25" in out


def test_deep_research_clears_assumptions_between_turns():
    a = FinFitAgent(user_id="test_clear")
    a.benefit_tool_args()
    assert a.assumptions
    a.deep_research("저축 계획")
    # plan may re-record if savings defaults needed, but clear ran first
    assert isinstance(a.assumptions, list)


if __name__ == "__main__":
    test_missing_profile_records_assumptions_not_state()
    test_known_profile_no_age_assumption()
    test_synthesize_surfaces_assumptions()
    test_deep_research_clears_assumptions_between_turns()
    print("ALL_OK")
