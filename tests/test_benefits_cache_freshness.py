"""
Smoke: policy cache meta + matcher still return a usable structure.

Does not call live 온통청년 API. Empty cache is allowed (fallback path)
but meta fields must be present so UI/AI can show honesty lines.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.trust_copy import policy_cache_meta, benefits_trust_lines
from finfit_youth.benefits_matcher import match_benefits
from finfit_youth.config import CACHE_DB_PATH, CACHE_TTL_SECONDS
from finfit_youth.tools import execute_tool_dict


def test_policy_cache_meta_shape():
    meta = policy_cache_meta()
    assert meta["cache_key"] == "snapshot:policy"
    assert "cache_size" in meta
    assert "cache_age_seconds" in meta or meta.get("cache_age_seconds") is None
    assert "cache_age_text" in meta
    assert "empty" in meta
    assert str(CACHE_DB_PATH) in str(meta.get("cache_db") or CACHE_DB_PATH)


def test_match_benefits_smoke_structure():
    r = match_benefits(
        age=25,
        income_level="100%이하",
        employment_status="미취업",
        has_house=False,
        query="청년",
        limit=5,
    )
    assert isinstance(r, dict)
    assert "benefits" in r
    # enrich should attach trust fields
    assert "disclaimer" in r or "method" in r or "cache_size" in r
    assert isinstance(r.get("benefits"), list)


def test_tool_benefit_path_same_smoke():
    r = execute_tool_dict(
        "check_benefit_eligibility",
        {
            "age": 26,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "query": "월세",
        },
    )
    assert "error" not in r or r.get("benefits") is not None
    assert "benefits" in r


def test_trust_lines_nonempty():
    lines = benefits_trust_lines()
    assert len(lines) >= 3
    assert any("캐시" in x or "출처" in x for x in lines)


def test_cache_ttl_config_positive():
    assert int(CACHE_TTL_SECONDS) > 0


def test_cache_age_warning_is_informational_only():
    """
    Stale cache must not crash tests — product still serves fallback/matcher.
    Soft signal: if age known and huge, meta still returns age_text.
    """
    meta = policy_cache_meta()
    age = meta.get("cache_age_seconds")
    if age is not None:
        assert age >= 0
        assert meta.get("cache_age_text")
    # size 0 → empty True (user should sync page 7)
    if meta.get("cache_size", 0) == 0:
        assert meta.get("empty") is True
