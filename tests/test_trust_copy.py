"""Provenance / disclaimer fields on benefits + stats results."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.benefits_matcher import match_benefits
from finfit_youth.gunsan_stats import get_gunsan_stat
from finfit_youth.trust_copy import (
    BENEFITS_DISCLAIMER,
    STATS_DISCLAIMER,
    benefits_trust_markdown,
    enrich_benefits_result,
    policy_cache_meta,
    stats_provenance,
    stats_trust_markdown,
)


def test_match_benefits_has_trust_fields():
    out = match_benefits(25, "100%이하", "미취업", False, query="취업", limit=5)
    assert out.get("disclaimer") == BENEFITS_DISCLAIMER
    assert out.get("method")
    assert "is_fallback" in out
    assert "cache_size" in out
    assert "cache_age_text" in out
    assert "신청 가능 확정" in (out.get("summary") or "") or "확정" in (out.get("disclaimer") or "")


def test_get_gunsan_stat_has_trust_fields():
    r = get_gunsan_stat("population")
    assert r.get("disclaimer") == STATS_DISCLAIMER
    assert r.get("method")
    assert "db_path" in r
    assert "core_sync_age_text" in r


def test_policy_cache_meta_shape():
    m = policy_cache_meta()
    assert "cache_size" in m
    assert "cache_age_text" in m
    assert "empty" in m


def test_stats_provenance_shape():
    p = stats_provenance()
    assert "db_path" in p
    assert "disclaimer" in p
    assert p["disclaimer"] == STATS_DISCLAIMER


def test_trust_markdown_nonempty():
    assert "출처" in benefits_trust_markdown() or "캐시" in benefits_trust_markdown()
    assert "DB" in stats_trust_markdown() or "한계" in stats_trust_markdown()


def test_enrich_idempotent_keys():
    base = {"data_source": "온통청년 정책 캐시", "cache_size": 1, "benefits": []}
    e1 = enrich_benefits_result(base)
    e2 = enrich_benefits_result(e1)
    assert e1["disclaimer"] == e2["disclaimer"]
    assert e2["is_fallback"] is False
