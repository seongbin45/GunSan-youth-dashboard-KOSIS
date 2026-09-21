"""
P1-1: plan()-only intent golden corpus.

Source of truth: tests/intent_golden.jsonl
- expect_tools: exact ordered tool list from plan().steps
- forbid_tools: must not appear
- expect_category: single get_gunsan_youth_stats category (if any)
- expect_clarify: plan.clarify flag
- optional first_goal / profile fields on UserState

Do not invent new keywords to silence failures without updating the corpus
with an explicit product decision.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent

GOLDEN_PATH = Path(__file__).resolve().parent / "intent_golden.jsonl"


def _load_cases() -> list[dict]:
    assert GOLDEN_PATH.is_file(), f"missing golden corpus: {GOLDEN_PATH}"
    rows = []
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(json.loads(line))
    return rows


CASES = _load_cases()
assert len(CASES) >= 50, f"golden corpus too small: {len(CASES)}"


def _apply_profile(agent: FinFitAgent, case: dict) -> None:
    agent.state.first_goal = case.get("first_goal")
    agent.state.age = None
    agent.state.income_level = None
    agent.state.employment_status = None
    agent.state.has_house = None
    agent.state.monthly_income = None
    for k, v in (case.get("profile") or {}).items():
        setattr(agent.state, k, v)
    # first_goal may also live only at top level
    if "first_goal" in case:
        agent.state.first_goal = case.get("first_goal")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.get("id") or c.get("q", "?")[:40])
def test_intent_golden_plan(case: dict):
    q = case["q"]
    a = FinFitAgent(user_id=f"golden_{case.get('id', 'x')}")
    a.clear_turn_scratch()
    _apply_profile(a, case)
    plan = a.plan(q)
    tools = [s["tool"] for s in (plan.get("steps") or [])]
    cats = [
        (s.get("args") or {}).get("category")
        for s in (plan.get("steps") or [])
        if s.get("tool") == "get_gunsan_youth_stats"
    ]

    assert tools == case.get("expect_tools", []), (
        f"[{case.get('id')}] tools {tools} != {case.get('expect_tools')} for {q!r}"
    )
    for t in case.get("forbid_tools") or []:
        assert t not in tools, f"[{case.get('id')}] forbid {t} in {tools} for {q!r}"

    if "expect_clarify" in case:
        assert bool(plan.get("clarify")) is bool(case["expect_clarify"]), (
            f"[{case.get('id')}] clarify {plan.get('clarify')} != {case['expect_clarify']} for {q!r}"
        )

    if case.get("expect_category") is not None:
        assert cats == [case["expect_category"]], (
            f"[{case.get('id')}] categories {cats} != {[case['expect_category']]} for {q!r}"
        )
    elif "get_gunsan_youth_stats" not in tools:
        assert cats == []


def test_golden_corpus_unique_ids():
    ids = [c.get("id") for c in CASES]
    assert all(ids), "every case needs id"
    assert len(ids) == len(set(ids)), "duplicate golden ids"


def test_golden_covers_three_pillars_and_clarify():
    tools_sets = {tuple(c.get("expect_tools") or []) for c in CASES}
    flat = {t for ts in tools_sets for t in ts}
    assert "check_benefit_eligibility" in flat
    assert "calculate_savings_plan" in flat
    assert "get_gunsan_youth_stats" in flat
    assert any(c.get("expect_clarify") for c in CASES)
    assert any(len(c.get("expect_tools") or []) >= 2 for c in CASES)
