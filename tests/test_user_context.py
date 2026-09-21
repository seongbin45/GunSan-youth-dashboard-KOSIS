"""UserContext: single sourced profile for pages + agent."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent, UserState
from finfit_youth.user_context import (
    build_user_context,
    apply_context_to_user_state,
    income_range_to_income_level,
    income_range_to_monthly_won,
    sync_session_and_state,
)


def test_empty_session_does_not_invent_age():
    ctx = build_user_context({})
    assert ctx.age is None
    assert ctx.monthly_income is None
    assert "age" in ctx.missing_for_benefits()
    assert "monthly_income" in ctx.missing_for_savings()


def test_benefit_profile_fills_eligibility_with_source():
    session = {
        "benefit_profile": {
            "age": 28,
            "income_ui": "100% 이하",
            "housing_ui": "무주택",
            "employment_ui": "취업자 (군산 소재 기업)",
            "keywords": ["취업자 (군산 소재 기업)"],
        }
    }
    ctx = build_user_context(session)
    assert ctx.age == 28
    assert ctx.sources.get("age") == "benefit_profile"
    assert ctx.income_level == "100%이하"
    assert ctx.sources.get("income_level") == "benefit_profile"
    assert ctx.employment_status == "취업자"
    assert ctx.has_house is False
    assert ctx.missing_for_benefits() == []


def test_benefit_profile_overrides_onboarding_derived_income_level():
    session = {
        "monthly_income_range": "50만원 미만",
        "benefit_profile": {
            "age": 30,
            "income_ui": "180% 이하",
            "housing_ui": "유주택",
            "employment_ui": "미취업 (구직 중)",
        },
    }
    ctx = build_user_context(session)
    assert ctx.income_level == "180%이하"
    assert ctx.sources["income_level"] == "benefit_profile"
    assert ctx.has_house is True


def test_ledger_income_and_spend():
    session = {
        "income": 2_500_000,
        "expenses": [{"amount": 500_000}, {"지출금액": "300000"}],
        "level": 6,
    }
    ctx = build_user_context(session)
    assert ctx.monthly_income == 2_500_000
    assert ctx.sources["monthly_income"] == "ledger"
    assert ctx.monthly_spend == 800_000
    assert ctx.savings_level == 6
    assert ctx.current_savings_rate is not None
    assert ctx.missing_for_savings() == []


def test_ledger_default_2m_does_not_stomp_agent_income():
    """H1: factory default income must not beat chat/agent monthly_income."""
    prior = UserState(monthly_income=2_500_000)
    session = {"income": 2_000_000}  # Ledger/Savings default, not touched
    ctx = build_user_context(session, prior=prior)
    assert ctx.monthly_income == 2_500_000
    assert ctx.sources.get("monthly_income") == "agent"


def test_ledger_touched_2m_can_override_agent():
    prior = UserState(monthly_income=2_500_000)
    session = {"income": 2_000_000, "income_touched": True}
    ctx = build_user_context(session, prior=prior)
    assert ctx.monthly_income == 2_000_000
    assert ctx.sources.get("monthly_income") == "ledger"


def test_h6_savings_level_syncs_to_tool_args():
    """Savings/Main session level must feed calculate_savings_plan."""
    a = FinFitAgent(user_id="h6_sl")
    a.clear_turn_scratch()
    a.state.monthly_income = 2_000_000
    session = {"income": 2_000_000, "income_touched": True, "level": 8}
    sync_session_and_state(session, a.state)
    assert a.state.savings_level == 8
    args = a.savings_tool_args(None, "저축 계획만 간단히")
    assert args["savings_level"] == 8
    assert args["income"] == 2_000_000


def test_h6_plan_uses_session_savings_level_not_hardcoded_5():
    """Regression: plan() used to force savings_level=5 and ignore session."""
    a = FinFitAgent(user_id="h6_plan")
    a.clear_turn_scratch()
    a.state.first_goal = None
    sync_session_and_state(
        {"income": 2_000_000, "income_touched": True, "level": 8}, a.state
    )
    plan = a.plan("저축 계획만 간단히")
    steps = [s for s in plan["steps"] if s["tool"] == "calculate_savings_plan"]
    assert len(steps) == 1
    assert steps[0]["args"]["savings_level"] == 8


def test_priority_benefit_age_over_prior_agent():
    prior = UserState(age=22)
    session = {"benefit_profile": {"age": 31, "income_ui": "100% 이하", "housing_ui": "무주택"}}
    ctx = build_user_context(session, prior=prior)
    assert ctx.age == 31


def test_onboarding_derived_income_level_beats_agent_prior():
    """H2: onboarding range must not lose to stale agent income_level."""
    prior = UserState(income_level="100%이하")  # e.g. old default/chat estimate
    session = {"monthly_income_range": "over200"}  # → 180%이하 derived
    ctx = build_user_context(session, prior=prior)
    assert ctx.income_level == "180%이하"
    assert ctx.sources.get("income_level") == "onboarding_derived"


def test_benefit_profile_still_beats_onboarding_derived():
    prior = UserState(income_level="100%이하")
    session = {
        "monthly_income_range": "over200",
        "benefit_profile": {
            "age": 26,
            "income_ui": "60% 이하",
            "housing_ui": "무주택",
            "employment_ui": "미취업 (구직 중)",
        },
    }
    ctx = build_user_context(session, prior=prior)
    assert ctx.income_level == "60%이하"
    assert ctx.sources.get("income_level") == "benefit_profile"
    assert ctx.sources["age"] == "benefit_profile"


def test_agent_sync_reduces_assumptions():
    a = FinFitAgent(user_id="test_uc_sync")
    a.state = UserState()  # clean
    a.clear_turn_scratch()
    session = {
        "benefit_profile": {
            "age": 27,
            "income_ui": "140% 이하",
            "housing_ui": "무주택",
            "employment_ui": "미취업 (구직 중)",
            "keywords": ["미취업 (구직 중)"],
        },
        "income": 2_000_000,
    }
    a.sync_from_session(session)
    assert a.state.age == 27
    assert a.state.income_level == "140%이하"
    assert a.state.monthly_income == 2_000_000
    a.clear_turn_scratch()
    args = a.benefit_tool_args()
    assert args["age"] == 27
    assert not any(x["field"] == "age" for x in a.assumptions)
    assert session.get("user_context", {}).get("age") == 27


def test_income_range_mapping_is_derived_only():
    lvl = income_range_to_income_level("150~200만원")
    assert lvl in ("140%이하", "150%이하", "180%이하", "100%이하")
    ctx = build_user_context({"monthly_income_range": "150~200만원"})
    assert ctx.income_level is not None
    assert ctx.sources.get("income_level") == "onboarding_derived"
    assert ctx.confidences.get("income_level", 1) < 0.9


def test_apply_does_not_clear_with_empty_context():
    state = UserState(age=29, income_level="100%이하")
    ctx = build_user_context({})
    apply_context_to_user_state(state, ctx)
    # empty ctx should not wipe existing state
    assert state.age == 29
    assert state.income_level == "100%이하"


def test_sync_session_and_state_roundtrip():
    state = UserState()
    session = {"user_level": "beginner", "first_goal": "비상금", "income": 1_800_000}
    ctx = sync_session_and_state(session, state)
    assert state.level == "beginner"
    assert state.first_goal == "비상금"
    assert state.monthly_income == 1_800_000
    assert "user_context" in session
    assert ctx.path_level == "beginner"


def test_h5_onboarding_range_mid_beats_ledger_default():
    """H5: under50 mid > ledger factory 2M so savings is not stuck at 200만."""
    ctx = build_user_context(
        {
            "monthly_income_range": "under50",
            "income": 2_000_000,  # untouched ledger default
        }
    )
    assert ctx.monthly_income == 400_000
    assert ctx.sources.get("monthly_income") == "onboarding_range_mid"
    assert ctx.confidences.get("monthly_income", 1) < 0.65


def test_h5_chat_income_beats_onboarding_range_mid():
    """H5: agent/chat monthly_income (0.65) still beats range mid (0.55)."""
    prior = UserState(monthly_income=2_500_000)
    ctx = build_user_context(
        {"monthly_income_range": "under50", "income": 2_000_000},
        prior=prior,
    )
    assert ctx.monthly_income == 2_500_000
    assert ctx.sources.get("monthly_income") == "agent"


def test_h5_ledger_touched_beats_onboarding_range_mid():
    ctx = build_user_context(
        {
            "monthly_income_range": "over200",
            "income": 2_000_000,
            "income_touched": True,
        }
    )
    assert ctx.monthly_income == 2_000_000
    assert ctx.sources.get("monthly_income") == "ledger"


def test_h5_savings_tool_uses_range_mid_not_silent_default():
    a = FinFitAgent(user_id="test_h5_sav")
    a.state = UserState()
    a.clear_turn_scratch()
    a.sync_from_session({"monthly_income_range": "100to150"})
    args = a.savings_tool_args(None, "")
    assert args["income"] == 1_250_000
    assert any(
        x.get("field") == "monthly_income" and x.get("source") == "onboarding_range_mid"
        for x in a.assumptions
    )


def test_income_range_to_monthly_won_ids():
    assert income_range_to_monthly_won("under50") == 400_000
    assert income_range_to_monthly_won("over200") == 2_500_000
    assert income_range_to_monthly_won("150~200만원") == 1_750_000
    assert income_range_to_monthly_won(None) is None
