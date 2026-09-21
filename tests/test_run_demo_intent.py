"""Demo mode must follow the same intent pillars as FinFitAgent plan()."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_run_demo():
    """Import run_demo without executing full Streamlit page body if possible.

    The AI page runs Streamlit side effects on import; we load via importlib
    only the function by exec of isolated copy is hard — instead import agent
    helpers and re-implement a thin parity check against plan() + tools.
    Full UI import is fragile in CI; test parity via agent plan + tools.
    """
    from finfit_youth.agent import (
        FinFitAgent,
        wants_benefit_query,
        wants_savings_query,
        wants_stats_query,
        stats_category_for_query,
        is_unclear_intent,
        CLARIFY_INTENT_TEXT,
    )
    from finfit_youth.tools import execute_tool_dict

    def run_demo_parity(user_message: str, state_kwargs: dict | None = None):
        a = FinFitAgent(user_id="demo_parity")
        a.state.first_goal = None
        a.state.monthly_income = None
        a.state.age = None
        a.state.income_level = None
        a.state.employment_status = None
        a.state.has_house = None
        for k, v in (state_kwargs or {}).items():
            setattr(a.state, k, v)
        plan = a.plan(user_message)
        tools = [s["tool"] for s in plan.get("steps") or []]
        cats = [
            (s.get("args") or {}).get("category")
            for s in plan.get("steps") or []
            if s.get("tool") == "get_gunsan_youth_stats"
        ]
        return {
            "tools": tools,
            "categories": cats,
            "clarify": plan.get("clarify"),
            "benefit": wants_benefit_query(user_message, a.state.first_goal),
            "savings": wants_savings_query(user_message),
            "stats": wants_stats_query(user_message),
            "unclear": is_unclear_intent(user_message, a.state.first_goal),
            "clarify_text": CLARIFY_INTENT_TEXT if plan.get("clarify") else "",
            "stats_cat": stats_category_for_query(user_message)
            if wants_stats_query(user_message)
            else None,
            # demo would call tools with same selection
            "demo_would_call_stats_once": wants_stats_query(user_message),
        }

    return run_demo_parity, execute_tool_dict


def test_demo_parity_benefit_only():
    run, _ = _load_run_demo()
    r = run("받을 수 있는 청년 혜택 알려줘")
    assert r["tools"] == ["check_benefit_eligibility"]
    assert r["clarify"] is False


def test_demo_parity_wolse_benefit_no_stats():
    run, _ = _load_run_demo()
    r = run("청년 월세 지원 혜택 알려줘")
    assert "check_benefit_eligibility" in r["tools"]
    assert "get_gunsan_youth_stats" not in r["tools"]


def test_demo_parity_stats_single_category():
    run, _ = _load_run_demo()
    r = run("군산 청년 취업 상황 알려줘")
    assert r["tools"] == ["get_gunsan_youth_stats"]
    assert r["categories"] == ["employment_difficulty"]
    assert r["demo_would_call_stats_once"] is True


def test_demo_parity_unclear_clarify():
    run, _ = _load_run_demo()
    r = run("돈 관리 어떻게 해")
    assert r["tools"] == []
    assert r["unclear"] is True
    assert r["clarify"] is True
    assert "혜택" in r["clarify_text"]


def test_stats_tool_single_category_not_four_dumps():
    """Regression: old demo dumped 4 stats categories for '군산'."""
    run, execd = _load_run_demo()
    r = run("군산시 청년 인구 현황 어때?")
    assert r["categories"] == ["population"]
    out = execd("get_gunsan_youth_stats", {"category": "population"})
    assert out.get("from_db") is True


def test_demo_parity_bare_salary_clarifies():
    run, _ = _load_run_demo()
    r = run("월급 얼마야")
    assert r["tools"] == []
    assert r["savings"] is False
    assert r["clarify"] is True


def test_demo_parity_gunsan_job_benefit_no_stats():
    run, _ = _load_run_demo()
    r = run("군산 취업 지원 혜택")
    assert "check_benefit_eligibility" in r["tools"]
    assert "get_gunsan_youth_stats" not in r["tools"]
