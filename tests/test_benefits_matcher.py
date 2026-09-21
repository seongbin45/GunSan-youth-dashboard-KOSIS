"""온통청년 policy cache matcher tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.benefits_matcher import (
    load_policy_snapshot,
    match_benefits,
    match_benefits_for_ui,
    normalize_income_level,
)
from finfit_youth.cache_store import CacheStore
from finfit_youth.config import match_benefits as config_match_benefits


def test_cache_has_policies_or_skip():
    snap = load_policy_snapshot()
    # Environment may lack cache; matcher must still return something via fallback
    out = match_benefits(25, "100%이하", "미취업", False, query="취업", limit=8)
    assert out["matched_count"] >= 1
    assert len(out["benefits"]) >= 1
    assert "summary" in out
    assert out["benefits"][0].get("name")


def test_life_stage_demotes_sinhon_without_signal():
    """Not 군산-first: demote 신혼 policies when user is 취준/미혼 (no 신혼 keyword)."""
    from finfit_youth.benefits_matcher import _life_stage_score_delta

    d = _life_stage_score_delta(
        title="군산시 신혼부부 전세자금 지원",
        blob="신혼부부 전세 이자 지원",
        query="나 25살 취준생 무주택 혜택",
        employment_status="미취업",
    )
    assert d <= -40

    d2 = _life_stage_score_delta(
        title="군산시 신혼부부 전세자금 지원",
        blob="신혼부부 전세",
        query="신혼부부 전세 지원",
        employment_status="취업자",
    )
    assert d2 == 0 or d2 > -10


def test_life_stage_keeps_startup_when_signaled_demotes_farm():
    from finfit_youth.benefits_matcher import _life_stage_score_delta

    # 창업 signal → do not demote 창업 platform
    d_start = _life_stage_score_delta(
        title="군산시 청년창업플랫폼 지원",
        blob="예비 청년 창업자 작업장 대여",
        query="창업하려는 26살 혜택",
        employment_status="창업자",
    )
    assert d_start >= -5

    # 농업 스마트팜 without farm signal → demote
    d_farm = _life_stage_score_delta(
        title="청년농업인 유치 임대스마트팜 건립",
        blob="청년농업인 스마트팜",
        query="창업하려는 26살 혜택",
        employment_status="창업자",
    )
    assert d_farm <= -30


def test_chwijun_top_not_dominated_by_sinhon_when_cache_rich():
    snap = load_policy_snapshot()
    if len(snap) < 50:
        return
    out = match_benefits(
        25,
        "100%이하",
        "미취업",
        False,
        query="나 25살 취준생, 군산 거주 무주택이야. 받을 수 있는 혜택 다 알려줘.",
        limit=5,
    )
    names = " ".join(b.get("name") or "" for b in out.get("benefits") or [])
    # Top-1 should not be a 신혼-only product for this profile
    top = (out.get("benefits") or [{}])[0].get("name") or ""
    assert "신혼부부" not in top


def test_query_boost_prefers_keyword_in_title_when_cache_present():
    snap = load_policy_snapshot()
    if len(snap) < 50:
        return  # CI without youth_cache.db
    out_job = match_benefits(25, "100%이하", "미취업", False, query="취업", limit=5)
    out_house = match_benefits(25, "100%이하", "미취업", False, query="월세", limit=5)
    assert out_job["data_source"].startswith("온통청년") or out_job["cache_size"] == 0
    # With real cache, results should exist and include source meta
    assert out_job["matched_count"] >= 1
    assert out_house["matched_count"] >= 1


def test_age_filter_excludes_impossible_ages_when_limits_present(tmp_path=None):
    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        store = CacheStore(path)
        store.set(
            "snapshot:policy",
            [
                {
                    "id": "p1",
                    "title": "전북 청년 취업 지원 테스트",
                    "summary": "전북 미취업 청년 취업 지원",
                    "region": "52111",
                    "raw": {
                        "plcyNm": "전북 청년 취업 지원 테스트",
                        "plcySprtCn": "취업 지원금",
                        "sprvsnInstCdNm": "전북특별자치도",
                        "sprtTrgtAgeLmtYn": "Y",
                        "sprtTrgtMinAge": 19,
                        "sprtTrgtMaxAge": 34,
                        "zipCd": "52111",
                        "lclsfNm": "일자리",
                        "mclsfNm": "취업",
                    },
                },
                {
                    "id": "p2",
                    "title": "시니어 전용",
                    "summary": "시니어",
                    "region": "52111",
                    "raw": {
                        "plcyNm": "시니어 전용",
                        "plcySprtCn": "시니어",
                        "sprvsnInstCdNm": "전북특별자치도",
                        "sprtTrgtAgeLmtYn": "Y",
                        "sprtTrgtMinAge": 50,
                        "sprtTrgtMaxAge": 70,
                        "zipCd": "52111",
                    },
                },
            ],
        )
        out = match_benefits(25, "100%이하", "미취업", False, query="취업", limit=10, store=store)
        names = [b["name"] for b in out["benefits"]]
        assert any("취업" in n for n in names)
        assert not any("시니어" in n for n in names)
        assert out["data_source"].startswith("온통청년")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_ui_adapter_and_config_delegate():
    assert normalize_income_level("100% 이하") == "100%이하"
    assert normalize_income_level("해당 없음 (소득 기준 초과)") == "소득기준초과"
    ui = match_benefits_for_ui(
        25,
        "100% 이하",
        "무주택",
        selected_keywords=["미취업 (구직 중)"],
        query="취업",
        limit=5,
    )
    assert "matched_policies" in ui
    assert "benefits" in ui
    assert ui["matched_count"] >= 1
    # config legacy API must hit same engine
    legacy = config_match_benefits(
        25, "100% 이하", True, ["미취업 (구직 중)"]
    )
    assert "matched_policies" in legacy
    assert legacy["matched_count"] >= 1


if __name__ == "__main__":
    test_cache_has_policies_or_skip()
    test_query_boost_prefers_keyword_in_title_when_cache_present()
    test_age_filter_excludes_impossible_ages_when_limits_present()
    test_ui_adapter_and_config_delegate()
    print("BENEFITS_MATCHER_OK")
