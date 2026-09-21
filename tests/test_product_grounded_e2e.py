"""
Product smoke: plan → execute tools → grounded answer (no LLM).

Locks the closed accuracy path for stats / savings / benefit / multi / clarify.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent
from finfit_youth.tools import execute_tool_dict
from finfit_youth.grounded_answer import try_grounded_answer, plan_external_tools_complete
from tests.test_agent_bench import run_research_loop


def _run_tools_from_plan(agent: FinFitAgent, query: str) -> list:
    plan = agent.deep_research(query)["plan"]
    results = []
    for step in plan.get("steps") or []:
        t = step["tool"]
        args = step.get("args") or {}
        out = execute_tool_dict(t, args)
        results.append({"tool": t, "input": args, "output": out})
    return results, plan


def test_e2e_stats_grounded():
    a = FinFitAgent(user_id="e2e_st")
    a.state.first_goal = None
    results, plan = _run_tools_from_plan(a, "군산시 청년 취업 상황 어때?")
    assert plan_external_tools_complete(plan, results)
    g = try_grounded_answer("군산시 청년 취업 상황 어때?", results, state=a.state, plan=plan)
    assert g["skip_llm"] is True
    assert "33.7" in (g["answer"] or "") or "33.7%" in (g["answer"] or "")


def test_e2e_savings_message_income():
    a = FinFitAgent(user_id="e2e_sv")
    a.state.first_goal = None
    a.state.monthly_income = 2_000_000
    q = "월급 250만원인데 저축 어떻게 해야 해?"
    results, plan = _run_tools_from_plan(a, q)
    assert results[0]["input"]["income"] == 2_500_000
    g = try_grounded_answer(q, results, state=a.state, plan=plan)
    assert g["skip_llm"] is True
    assert "2,500,000" in (g["answer"] or "") or "2500000" in (g["answer"] or "").replace(",", "")


def test_e2e_benefit_profile_parse():
    a = FinFitAgent(user_id="e2e_bf")
    a.state.first_goal = None
    a.state.age = None
    a.state.employment_status = None
    a.state.has_house = None
    q = "나 25살 취준생, 군산 거주 무주택이야. 받을 수 있는 혜택 다 알려줘."
    results, plan = _run_tools_from_plan(a, q)
    assert results[0]["input"]["age"] == 25
    assert results[0]["input"]["employment_status"] == "미취업"
    assert results[0]["input"]["has_house"] is False
    g = try_grounded_answer(q, results, state=a.state, plan=plan)
    assert g["skip_llm"] is True
    assert "혜택" in (g["answer"] or "")


def test_e2e_multi_benefit_savings():
    a = FinFitAgent(user_id="e2e_mu")
    a.state.first_goal = None
    a.state.monthly_income = 2_500_000
    q = "창업하려는 26살인데 혜택이랑 저축 계획 같이 알려줘."
    results, plan = _run_tools_from_plan(a, q)
    tools = [r["tool"] for r in results]
    assert "check_benefit_eligibility" in tools
    assert "calculate_savings_plan" in tools
    g = try_grounded_answer(q, results, state=a.state, plan=plan)
    assert g["skip_llm"] is True
    assert g["mode"] == "multi"
    assert "---" in (g["answer"] or "")
    assert "저축" in (g["answer"] or "")


def test_e2e_clarify():
    a = FinFitAgent(user_id="e2e_cl")
    a.state.first_goal = None
    q = "도와줘"
    plan = a.deep_research(q)["plan"]
    assert plan.get("clarify") is True
    g = try_grounded_answer(q, [], state=a.state, plan=plan)
    assert g["skip_llm"] is True
    assert g["mode"] == "clarify"


def test_research_loop_shallow_few_internals():
    """Accuracy path: no assess/prepare pile-up on single-tool turns."""
    a = FinFitAgent(user_id="e2e_loop")
    a.state.first_goal = None
    tools, final, assumptions, internals, depth, tool_calls = run_research_loop(
        a, "군산시 청년 취업 상황 어때?"
    )
    assert tools == ["get_gunsan_youth_stats"]
    assert final == "synthesize"
    assert "assess_coverage" not in internals
    assert "prepare_synthesis" not in internals
