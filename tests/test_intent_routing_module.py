"""intent_routing is canonical; agent re-exports for back-compat."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import finfit_youth.agent as agent_mod
import finfit_youth.intent_routing as route


def test_agent_reexports_routing_symbols():
    assert agent_mod.wants_stats_query is route.wants_stats_query
    assert agent_mod.wants_savings_query is route.wants_savings_query
    assert agent_mod.wants_benefit_query is route.wants_benefit_query
    assert agent_mod.stats_category_for_query is route.stats_category_for_query
    assert agent_mod.is_unclear_intent is route.is_unclear_intent
    assert agent_mod.CLARIFY_INTENT_TEXT is route.CLARIFY_INTENT_TEXT


def test_routing_module_smoke():
    assert route.wants_benefit_query("청년 혜택") is True
    assert route.wants_savings_query("저축 계획") is True
    assert route.stats_category_for_query("군산 청년 취업 상황") == "employment_difficulty"
    assert route.is_unclear_intent("도와줘") is True
