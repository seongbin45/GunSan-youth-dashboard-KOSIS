"""AI tool registry (finfit_youth.tools) unit tests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.tools import (
    BASE_TOOLS,
    TOOL_HANDLERS,
    execute_tool,
    execute_tool_dict,
    tool_savings_plan,
)


def test_base_tools_names_match_handlers():
    names = {t["name"] for t in BASE_TOOLS}
    assert names == set(TOOL_HANDLERS.keys())
    assert "check_benefit_eligibility" in names
    assert "get_gunsan_youth_stats" in names
    assert "calculate_savings_plan" in names


def test_execute_unknown_tool():
    out = json.loads(execute_tool("nope", {}))
    assert "error" in out


def test_savings_plan_ok():
    r = tool_savings_plan(2_000_000, 5)
    assert r["monthly_savings"] == 500_000
    assert r["monthly_fixed"] == 1_100_000
    assert "error" not in r


def test_savings_plan_bad_level():
    r = tool_savings_plan(2_000_000, 99)
    assert "error" in r


def test_benefit_tool_has_disclaimer():
    r = execute_tool_dict(
        "check_benefit_eligibility",
        {
            "age": 25,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "query": "취업",
        },
    )
    assert r.get("matched_count", 0) >= 1
    assert r.get("disclaimer")
    assert "is_fallback" in r


def test_stats_tool_from_db():
    r = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    assert r.get("from_db") is True
    assert r.get("figures", {}).get("gunsan_youth_18_39") == 56117
    assert r.get("disclaimer")
