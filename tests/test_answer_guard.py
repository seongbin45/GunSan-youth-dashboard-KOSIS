"""P0-2/3: allowed figures block + soft numeric check."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.answer_guard import (
    build_allowed_figures_block,
    extract_allowed_numbers,
    soft_check_answer,
)
from finfit_youth.agent import FinFitAgent
from finfit_youth.tools import execute_tool_dict


def test_extract_from_stats_tool():
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    allowed = extract_allowed_numbers(
        [{"tool": "get_gunsan_youth_stats", "output": out}]
    )
    assert 56117 in allowed or any(abs(n - 56117) < 1 for n in allowed)


def test_soft_check_flags_invented_population():
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    tr = [{"tool": "get_gunsan_youth_stats", "output": out}]
    bad = soft_check_answer(
        "군산 청년 인구는 99,999명입니다.",
        tr,
    )
    assert bad["ok"] is False
    assert any(abs(n - 99999) < 1 for n in bad["unmatched"])


def test_soft_check_accepts_tool_number():
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    tr = [{"tool": "get_gunsan_youth_stats", "output": out}]
    # use grounded figure from tool
    fig = (out.get("figures") or {}).get("gunsan_youth_18_39") or 56117
    good = soft_check_answer(
        f"군산 청년(18~39) 인구는 약 {int(fig):,}명입니다.",
        tr,
    )
    assert good["ok"] is True


def test_clarify_only_flags_large_numbers():
    r = soft_check_answer(
        "인구가 50000명쯤 됩니다.",
        [],
        clarify_only=True,
    )
    assert r["ok"] is False


def test_allowed_figures_block_in_prepare():
    a = FinFitAgent(user_id="guard_prep")
    a.clear_turn_scratch()
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    steps = [{"tool": "get_gunsan_youth_stats", "input": {"category": "population"}, "output": out}]
    a.ingest_tool_result("get_gunsan_youth_stats", {"category": "population"}, out)
    ctx = a.prepare_synthesis_context("군산시 청년 인구 현황 어때?", steps)
    assert "ALLOWED FIGURES" in ctx
    assert "56117" in ctx or "56,117" in ctx or "56.117" in ctx


def test_synthesize_final_prepends_warning_on_hallucination():
    a = FinFitAgent(user_id="guard_syn")
    a.clear_turn_scratch()
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    steps = [{"tool": "get_gunsan_youth_stats", "output": out}]
    text = a.synthesize_final(
        "군산 청년은 888888명입니다. 충분히 긴 답변으로 soft check를 통과할 본문 길이입니다.",
        steps,
        "군산시 청년 인구 현황 어때?",
    )
    assert "숫자 검증 경고" in text
    g = getattr(a, "_last_answer_guard", {})
    assert g.get("ok") is False


def test_build_block_no_tools():
    block = build_allowed_figures_block([])
    assert "none from tools" in block.lower() or "No external" in block


def test_year_2026_in_benefit_name_not_flagged():
    """Live log: soft-check warned on 2026 from 청년미래적금(2026신설)."""
    from finfit_youth.answer_guard import soft_check_answer, is_calendar_year

    assert is_calendar_year(2026) is True
    out = execute_tool_dict(
        "get_gunsan_youth_stats", {"category": "employment_difficulty"}
    )
    tr = [{"tool": "get_gunsan_youth_stats", "output": out}]
    answer = (
        "1위 33.7%, 2위 25.0%, 3위 12.4%입니다. "
        "알고 있는 혜택: 청년미래적금(2026신설), 청년도약계좌. "
        "충분히 긴 본문으로 soft-check 길이를 채웁니다."
    )
    r = soft_check_answer(answer, tr)
    assert r["ok"] is True, r.get("unmatched")
    assert 2026 not in (r.get("unmatched") or [])
