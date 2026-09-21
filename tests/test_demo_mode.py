"""P0-4: demo surfaces assumptions; no silent defaults."""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.demo_mode import run_demo_turn
from finfit_youth.tools import execute_tool


def _empty_state(**kw):
    base = dict(
        age=None,
        income_level=None,
        employment_status=None,
        has_house=None,
        monthly_income=None,
        first_goal=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_benefit_empty_profile_shows_assumptions():
    recorded = []

    def rec(f, v, r):
        recorded.append((f, v, r))

    text, steps = run_demo_turn(
        "받을 수 있는 청년 혜택 알려줘",
        state=_empty_state(),
        execute_tool=execute_tool,
        record_assumption=rec,
    )
    assert "이번 답변에 쓰인 가정" in text
    assert "age" in text
    assert any(s["tool"] == "check_benefit_eligibility" for s in steps)
    assert recorded  # agent-style record hook called


def test_full_profile_no_assumption_block_for_benefit():
    text, steps = run_demo_turn(
        "받을 수 있는 청년 혜택 알려줘",
        state=_empty_state(
            age=26,
            income_level="100%이하",
            employment_status="미취업",
            has_house=False,
        ),
        execute_tool=execute_tool,
    )
    assert "이번 답변에 쓰인 가정" not in text
    assert any(s["tool"] == "check_benefit_eligibility" for s in steps)


def test_savings_empty_income_assumes():
    text, steps = run_demo_turn(
        "저축 계획만 간단히",
        state=_empty_state(),
        execute_tool=execute_tool,
    )
    assert "monthly_income" in text or "월소득" in text
    assert "이번 답변에 쓰인 가정" in text
    assert any(s["tool"] == "calculate_savings_plan" for s in steps)


def test_clarify_no_false_assumptions():
    text, steps = run_demo_turn(
        "도와줘",
        state=_empty_state(),
        execute_tool=execute_tool,
    )
    assert "의도 확인" in text or "혜택" in text
    assert "이번 답변에 쓰인 가정" not in text
    assert not any(
        s["tool"] in (
            "check_benefit_eligibility",
            "calculate_savings_plan",
            "get_gunsan_youth_stats",
        )
        for s in steps
    )
