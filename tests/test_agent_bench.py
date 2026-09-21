"""
Step-2 bench: dry-run research_step pipeline (no LLM API).

Validates tool selection + assumption honesty against agent_bench_cases.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent
from tests.agent_bench_cases import BENCH_CASES


def _fake_tool(name: str, args: dict) -> dict:
    if name == "check_benefit_eligibility":
        return {
            "matched_count": 2,
            "benefits": [
                {"name": "청년도약계좌", "benefit": "예시"},
                {"name": "K-패스", "benefit": "예시"},
            ],
            "summary": "2건",
        }
    if name == "calculate_savings_plan":
        return {
            "monthly_savings": 400000,
            "savings_rate": "17%",
            "monthly_income": args.get("income", 0),
        }
    if name == "get_gunsan_youth_stats":
        return {"data": "예시 통계", "insight": "ok", "category": args.get("category")}
    return {"ok": True}


def apply_profile(agent: FinFitAgent, profile: Dict[str, Any]) -> None:
    # Reset key fields for isolation
    agent.state.age = None
    agent.state.income_level = None
    agent.state.employment_status = None
    agent.state.has_house = None
    agent.state.monthly_income = None
    agent.state.monthly_spend = None
    agent.state.first_goal = None
    agent.state.active_goals = []
    agent.state.known_benefits = []
    agent.state.last_research_was_insufficient = False
    agent.research_trajectory = []
    for k, v in (profile or {}).items():
        setattr(agent.state, k, v)


def run_research_loop(
    agent: FinFitAgent, query: str, max_rounds: int = 14
) -> Tuple[List[str], str, List[dict], List[str], str, List[dict]]:
    """Returns (tools, final, assumptions, internals, depth, tool_calls[{tool,args}])."""
    agent.deep_research(query)
    obs: List[dict] = []
    tools: List[str] = []
    tool_calls: List[dict] = []
    internals: List[str] = []
    last_depth = ""
    for _ in range(max_rounds):
        d = agent.research_step(query, previous_results=obs)
        last_action = d.get("action") or ""
        last_depth = d.get("depth") or last_depth
        if last_action == "tool":
            tname = d["tool"]
            targs = d.get("args") or {}
            tools.append(tname)
            tool_calls.append({"tool": tname, "args": dict(targs)})
            out = _fake_tool(tname, targs)
            obs.append({"tool": tname, "input": targs, "output": out})
        elif last_action == "internal":
            itype = d.get("internal_type") or "reason"
            internals.append(itype)
            obs.append({
                "tool": f"_internal_{itype}",
                "input": {},
                "output": {"summary": (d.get("summary") or "")[:80]},
            })
        elif last_action == "synthesize":
            return tools, "synthesize", list(agent.assumptions), internals, last_depth, tool_calls
        else:
            return (
                tools,
                last_action or "unknown",
                list(agent.assumptions),
                internals,
                last_depth,
                tool_calls,
            )
    return tools, "timeout", list(agent.assumptions), internals, last_depth, tool_calls


def _match_args_contains(args: dict, want: dict) -> bool:
    return all(args.get(k) == v for k, v in want.items())


def run_case(case: dict) -> List[str]:
    errors: List[str] = []
    agent = FinFitAgent(user_id=f"bench_{case['id']}")
    apply_profile(agent, case.get("profile") or {})
    tools, final, assumptions, internals, depth, tool_calls = run_research_loop(
        agent, case["query"]
    )
    tool_set = set(tools)
    assum_fields = {a.get("field") for a in assumptions}

    for t in case.get("expect_tools") or []:
        if t not in tool_set:
            errors.append(f"missing tool {t}; got {tools}")

    for t in case.get("forbid_tools") or []:
        if t in tool_set:
            errors.append(f"unexpected tool {t}; got {tools}")

    # Precise arg checks (e.g. stats category)
    for spec in case.get("expect_tool_args") or []:
        tname = spec.get("tool")
        want = spec.get("args_contains") or {}
        ok = any(
            c.get("tool") == tname and _match_args_contains(c.get("args") or {}, want)
            for c in tool_calls
        )
        if not ok:
            errors.append(
                f"missing tool args {tname} contains {want}; calls={tool_calls}"
            )

    for spec in case.get("forbid_tool_args") or []:
        tname = spec.get("tool")
        want = spec.get("args_contains") or {}
        bad = any(
            c.get("tool") == tname and _match_args_contains(c.get("args") or {}, want)
            for c in tool_calls
        )
        if bad:
            errors.append(
                f"forbidden tool args {tname} contains {want}; calls={tool_calls}"
            )

    for f in case.get("expect_assumption_fields") or []:
        if f not in assum_fields:
            errors.append(f"missing assumption {f}; got {assum_fields}")

    for f in case.get("forbid_assumption_fields") or []:
        if f in assum_fields:
            errors.append(f"unexpected assumption {f}; got {assum_fields}")

    if case.get("must_synthesize", True) and final != "synthesize":
        errors.append(f"expected synthesize, got {final}")

    if "expect_depth" in case and depth != case["expect_depth"]:
        errors.append(f"expected depth={case['expect_depth']}, got {depth}")

    if "expect_max_internals" in case and len(internals) > case["expect_max_internals"]:
        errors.append(
            f"too many internals {len(internals)}>{case['expect_max_internals']}: {internals}"
        )

    if "forbid_internal_kinds" in case:
        for k in case["forbid_internal_kinds"]:
            if k in internals:
                errors.append(f"unexpected internal {k} in {internals}")

    # Honesty: empty profile benefit path should not invent permanent age
    if case["id"] == "benefit_only_empty_profile":
        if agent.state.age is not None:
            errors.append(f"state.age polluted: {agent.state.age}")

    return errors


def test_all_bench_cases():
    failures = []
    for case in BENCH_CASES:
        errs = run_case(case)
        if errs:
            failures.append((case["id"], errs))
    if failures:
        msg = "\n".join(f"- {cid}: {errs}" for cid, errs in failures)
        raise AssertionError(f"{len(failures)}/{len(BENCH_CASES)} cases failed:\n{msg}")


def test_bench_count():
    assert len(BENCH_CASES) >= 20, "bench should stay meaningful (≥20 cases)"


def test_stats_cases_declare_category_args():
    """Regression guard: stats-related cases must pin category via expect_tool_args."""
    stats_ids = {
        "gunsan_stats_only",
        "employment_stats",
        "employment_count_stats",
        "employment_difficulty_stats",
        "housing_stats",
        "income_stats",
    }
    found = {c["id"] for c in BENCH_CASES if c["id"] in stats_ids}
    assert found == stats_ids
    for c in BENCH_CASES:
        if c["id"] not in stats_ids:
            continue
        specs = c.get("expect_tool_args") or []
        assert any(
            s.get("tool") == "get_gunsan_youth_stats"
            and (s.get("args_contains") or {}).get("category")
            for s in specs
        ), f"{c['id']} missing category expect_tool_args"


def test_research_step_keeps_plan_stats_category():
    """First tool call category must match plan() for the same query (no silent override)."""
    from finfit_youth.agent import FinFitAgent

    cases = [
        ("군산시 청년 인구 현황 어때?", "population"),
        ("군산 청년 취업 상황 알려줘", "employment_difficulty"),
        ("전북 청년 취업자 수 통계 알려줘", "employment_count"),
        ("군산 청년 주택 소유율 통계 있어?", "housing"),
        ("군산 청년 임금 분포 통계 알려줘", "income"),
    ]
    for query, cat in cases:
        a = FinFitAgent(user_id=f"cat_stable_{cat}")
        a.state.first_goal = None
        a.clear_turn_scratch()
        a.deep_research(query)
        plan = a.plan(query)
        plan_stats = [
            s for s in (plan.get("steps") or []) if s.get("tool") == "get_gunsan_youth_stats"
        ]
        assert plan_stats, f"plan missing stats for {query!r}"
        assert plan_stats[0]["args"].get("category") == cat, plan_stats[0]
        step = a.research_step(query, previous_results=[])
        assert step.get("action") == "tool"
        assert step.get("tool") == "get_gunsan_youth_stats"
        assert (step.get("args") or {}).get("category") == cat, step


if __name__ == "__main__":
    test_bench_count()
    test_all_bench_cases()
    print(f"BENCH_OK cases={len(BENCH_CASES)}")
    for case in BENCH_CASES:
        agent = FinFitAgent(user_id=f"report_{case['id']}")
        apply_profile(agent, case.get("profile") or {})
        tools, final, assumptions, internals, depth, tool_calls = run_research_loop(
            agent, case["query"]
        )
        print(
            f"  [{case['id']}] depth={depth} tools={tools} calls={tool_calls} "
            f"internals={internals} final={final} "
            f"assumptions={[a['field'] for a in assumptions]}"
        )
