"""Unit tests for stats intent routing (plan / critique category source of truth)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import (
    FinFitAgent,
    wants_stats_query,
    wants_savings_query,
    wants_benefit_query,
    stats_category_for_query,
    is_unclear_intent,
    CLARIFY_INTENT_TEXT,
)


def test_wants_stats_not_triggered_by_salary_savings_only():
    assert wants_stats_query("월급 기준으로 저축 계획 세워줘") is False
    assert wants_stats_query("생활비 아끼고 저축하려면?") is False


def test_wants_stats_not_triggered_by_benefit_phrasing():
    """Benefit/support questions must not pull KOSIS tools."""
    assert wants_stats_query("전세 보증 관련 지원 있어?") is False
    assert wants_stats_query("청년 월세 지원 혜택 알려줘") is False
    assert wants_stats_query("월세 지원금 자격") is False
    assert wants_stats_query("군산 거주인데 받을 수 있는 혜택 뭐 있어?") is False
    # 군산+취업/주택+지원/혜택 without 통계·현황 → benefit only
    assert wants_stats_query("군산 취업 지원 혜택") is False
    assert wants_stats_query("군산 청년 일자리 지원금") is False
    assert wants_stats_query("군산 주택 지원 혜택") is False
    assert wants_stats_query("군산 주택 현황") is True


def test_bare_salary_or_calc_not_savings():
    """'월급 얼마야' / '계산 좀' must not open savings tool."""
    assert wants_savings_query("월급 얼마야") is False
    assert wants_savings_query("계산 좀") is False
    assert is_unclear_intent("월급 얼마야", None) is True
    assert is_unclear_intent("계산 좀", None) is True
    # companion words still work
    assert wants_savings_query("월급 기준으로 저축 계획 세워줘") is True
    assert wants_savings_query("월급 예산 나누기") is True
    assert wants_savings_query("저축액 계산해줘") is True


def test_wants_stats_population_employment_housing():
    assert wants_stats_query("군산시 청년 인구 현황 어때?") is True
    assert wants_stats_query("군산 청년 취업 상황 알려줘") is True
    assert wants_stats_query("주택 소유율 통계") is True
    assert wants_stats_query("전세 통계 있어?") is True
    assert wants_stats_query("군산 청년 임금 분포 통계") is True


def test_category_population():
    assert stats_category_for_query("군산시 청년 인구 현황 어때?") == "population"


def test_category_employment_difficulty():
    assert stats_category_for_query("군산 청년 취업 상황 알려줘") == "employment_difficulty"
    assert stats_category_for_query("군산 취업 어려움 원인이 뭐야?") == "employment_difficulty"


def test_category_employment_count():
    assert stats_category_for_query("전북 청년 취업자 수 통계 알려줘") == "employment_count"


def test_category_housing():
    assert stats_category_for_query("군산 청년 주택 소유율 통계 있어?") == "housing"


def test_category_income():
    assert stats_category_for_query("군산 청년 임금 분포 통계") == "income"


def test_refine_plan_uses_query_category_not_population():
    a = FinFitAgent(user_id="refine_cat_tmp")
    a.state.first_goal = None
    plan = {"plan_text": "empty", "steps": [], "user_goal": None}
    critique = "질문 범위 내 부족: 통계_도구_미실행."
    msg = "군산 청년 취업 상황 알려줘"
    refined = a.refine_plan_with_critique(plan, critique, [], user_message=msg)
    stats_steps = [s for s in refined["steps"] if s["tool"] == "get_gunsan_youth_stats"]
    assert len(stats_steps) == 1
    assert stats_steps[0]["args"]["category"] == "employment_difficulty"


def test_income_alone_does_not_force_savings_tool():
    a = FinFitAgent(user_id="no_auto_sav")
    a.state.monthly_income = 2_500_000
    a.state.age = 26
    a.state.income_level = "100%이하"
    a.state.employment_status = "미취업"
    a.state.has_house = False
    a.state.first_goal = None
    plan = a.plan("받을 수 있는 청년 혜택 알려줘")
    tools = [s["tool"] for s in plan.get("steps") or []]
    assert "check_benefit_eligibility" in tools
    assert "calculate_savings_plan" not in tools


def test_first_goal_open_ended_triggers_benefit_only():
    assert wants_benefit_query("뭐부터 하면 좋을까?", first_goal="노트북") is True
    assert wants_savings_query("뭐부터 하면 좋을까?") is False
    a = FinFitAgent(user_id="goal_open")
    a.state.first_goal = "노트북"
    a.state.age = 24
    a.state.income_level = "100%이하"
    a.state.employment_status = "취업자"
    a.state.has_house = False
    a.state.monthly_income = 2_000_000
    plan = a.plan("뭐부터 하면 좋을까?")
    tools = [s["tool"] for s in plan.get("steps") or []]
    assert tools == ["check_benefit_eligibility"]


def test_first_goal_does_not_force_benefit_on_pure_savings_or_stats():
    assert wants_benefit_query("저축 계획만 간단히", first_goal="노트북") is False
    assert wants_benefit_query("군산시 청년 인구 현황 어때?", first_goal="노트북") is False
    a = FinFitAgent(user_id="goal_scoped")
    a.state.first_goal = "노트북"
    a.state.monthly_income = 2_000_000
    plan_s = a.plan("저축 계획만 간단히")
    assert [s["tool"] for s in plan_s["steps"]] == ["calculate_savings_plan"]
    plan_p = a.plan("군산시 청년 인구 현황 어때?")
    tools_p = [s["tool"] for s in plan_p["steps"]]
    assert tools_p == ["get_gunsan_youth_stats"]
    assert plan_p["steps"][0]["args"]["category"] == "population"


def test_unclear_intent_sets_clarify_and_no_tools():
    for q in ("취업 관련 도와줘", "군산 살아", "돈 관리 어떻게 해", "안녕"):
        assert is_unclear_intent(q, None) is True
        a = FinFitAgent(user_id="unclear_p")
        a.state.first_goal = None
        plan = a.plan(q)
        assert plan.get("steps") == []
        assert plan.get("clarify") is True
        assert "혜택" in (plan.get("clarify_text") or CLARIFY_INTENT_TEXT)


def test_unclear_research_step_clarifies_then_synthesizes():
    from tests.test_agent_bench import run_research_loop

    a = FinFitAgent(user_id="unclear_loop")
    a.state.first_goal = None
    tools, final, assumptions, internals, depth, tool_calls = run_research_loop(
        a, "돈 관리 어떻게 해"
    )
    assert tools == []
    assert tool_calls == []
    assert final == "synthesize"
    assert "clarify_intent" in internals
    # prepare_synthesis optional — accuracy path synthesizes right after clarify


def test_refine_plan_income_and_count_categories():
    a = FinFitAgent(user_id="refine_multi_tmp")
    a.state.first_goal = None
    base = {"plan_text": "empty", "steps": [], "user_goal": None}
    critique = "질문 범위 내 부족: 통계_도구_미실행."
    for msg, cat in (
        ("군산 청년 임금 분포 통계", "income"),
        ("전북 청년 취업자 수 통계", "employment_count"),
        ("군산 청년 주택 소유율 통계", "housing"),
    ):
        refined = a.refine_plan_with_critique(dict(base), critique, [], user_message=msg)
        stats = [s for s in refined["steps"] if s["tool"] == "get_gunsan_youth_stats"]
        assert len(stats) == 1
        assert stats[0]["args"]["category"] == cat, (msg, stats)
