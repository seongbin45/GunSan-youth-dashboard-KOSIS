"""GunSan stats from SQLite — shared by AI tool and page 6 charts."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.gunsan_stats import (
    get_gunsan_stat,
    DEFAULT_DB,
    DASHBOARD_TABLES,
    load_dashboard_data,
    read_table,
    resolve_db_path,
)


def test_db_exists_in_project():
    assert DEFAULT_DB.is_file(), f"expected DB at {DEFAULT_DB}"
    assert resolve_db_path().is_file()


def test_population_from_db():
    r = get_gunsan_stat("population")
    assert r.get("from_db") is True
    assert r.get("figures", {}).get("gunsan_youth_18_39") == 56117
    assert "56,117" in r.get("data", "") or "56117" in r.get("data", "")
    assert "gunsan_youth_data.db" in r.get("source", "")


def test_housing_from_db():
    r = get_gunsan_stat("housing")
    assert r.get("from_db") is True
    rate = r.get("figures", {}).get("youth_ownership_rate_pct")
    assert rate is not None
    assert "소유" in r.get("data", "")


def test_income_from_db():
    r = get_gunsan_stat("income")
    assert r.get("from_db") is True
    assert r.get("figures", {}).get("bands")
    assert "임금" in r.get("data", "") or "만원" in r.get("data", "")


def test_employment_difficulty_gunsan_percent():
    r = get_gunsan_stat("employment_difficulty")
    assert r.get("from_db") is True
    assert r.get("category") == "employment_difficulty"
    assert r.get("metric", {}).get("geography") == "군산시"
    assert r.get("metric", {}).get("unit") == "percent"
    top = (r.get("figures") or {}).get("difficulty_top") or []
    assert top and top[0]["pct"] == 33.7
    assert "군산" in r.get("data", "")


def test_employment_count_quarterly_mean_not_raw_sum():
    """Must not sum all gender×quarter rows (old bug → 987)."""
    r = get_gunsan_stat("employment_count")
    assert r.get("from_db") is True
    assert r.get("metric", {}).get("geography", "").startswith("전북")
    mean = (r.get("figures") or {}).get("youth_15_39_quarterly_mean")
    assert mean is not None
    # Correct quarterly mean is ~247 (563+424)/4 style? men 563 women 424 is full year sum
    # quarterly mean of youth should be around 987/4 ≈ 246.75
    assert 200 < float(mean) < 350, f"unexpected mean {mean} (possible double-count)"
    assert "분기평균" in r.get("data", "")
    assert "군산시 단독이 아님" in r.get("data", "")
    # Honest unit labeling (no fake '명' without table unit column)
    m = r.get("metric") or {}
    assert m.get("unit_label_ko")
    assert "천명" in (m.get("unit_label_ko") or "") or "천명" in (m.get("unit_note") or "")
    assert "통상" in (r.get("data") or "") or "천명" in (r.get("data") or "")


def test_employment_bundle_keeps_both_metrics():
    r = get_gunsan_stat("employment")
    assert r.get("from_db") is True
    figs = r.get("figures") or {}
    assert figs.get("bundle") is True
    assert figs.get("difficulty")
    assert figs.get("count")
    assert "difficulty" in (r.get("insight") or "").lower() or "어려움" in (r.get("insight") or "")


def test_employment_count_matches_pie_share_inputs():
    """Page 6 pie must use same youth/total means (no raw panel SUM)."""
    r = get_gunsan_stat("employment_count")
    f = r.get("figures") or {}
    youth = float(f["youth_15_39_quarterly_mean"])
    total = float(f["all_ages_quarterly_mean"])
    assert total > youth > 0
    share = youth / total * 100
    assert abs(share - float(f["youth_share_pct"])) < 0.05


def test_unknown_category():
    r = get_gunsan_stat("not_a_cat")
    assert "error" in r


def test_fallback_missing_db(tmp_path):
    missing = tmp_path / "nope.db"
    r = get_gunsan_stat("population", db_path=missing)
    assert r.get("from_db") is False
    assert "fallback" in (r.get("source") or "").lower() or "DB" in r.get("data", "")


def test_load_dashboard_data_core_tables():
    """Page 6 and AI must share the same loader / table constants."""
    bundle = load_dashboard_data()
    assert bundle["ok"] is True
    assert Path(bundle["db_path"]).is_file()
    # Core KOSIS tables used by charts + AI
    for key in ("housing", "wage", "health", "population_success"):
        assert key in DASHBOARD_TABLES
        df = bundle["tables"][key]
        assert df is not None
        assert not df.empty, f"{key} should have rows in project DB"
        assert key not in bundle["missing"]


def test_dashboard_housing_matches_stat_figures():
    """Chart table and get_gunsan_stat(housing) must describe the same DB rows."""
    bundle = load_dashboard_data()
    house = bundle["tables"]["housing"]
    assert not house.empty
    # 18~39 rate row must exist in table if stat reports it
    r = get_gunsan_stat("housing")
    rate = r.get("figures", {}).get("youth_ownership_rate_pct")
    assert rate is not None
    rates = house[house["C2_NM"].astype(str).str.contains("비율", na=False)]
    youth = rates[rates["C1_NM"].astype(str).str.contains("18~39", na=False)]
    assert not youth.empty
    table_rate = float(youth.iloc[0]["DT"])
    assert abs(table_rate - float(rate)) < 1e-6


def test_read_table_logical_key():
    df = read_table("wage")
    assert not df.empty
    assert "C2_NM" in df.columns or "DT" in df.columns


def test_load_dashboard_missing_db(tmp_path):
    bundle = load_dashboard_data(db_path=tmp_path / "absent.db")
    assert bundle["ok"] is False
    assert bundle["missing"]
    assert all(bundle["tables"][k].empty for k in DASHBOARD_TABLES)


if __name__ == "__main__":
    test_db_exists_in_project()
    test_population_from_db()
    test_housing_from_db()
    test_income_from_db()
    test_employment_difficulty_gunsan_percent()
    test_employment_count_quarterly_mean_not_raw_sum()
    test_employment_bundle_keeps_both_metrics()
    test_unknown_category()
    test_load_dashboard_data_core_tables()
    test_dashboard_housing_matches_stat_figures()
    test_read_table_logical_key()
    print("GUNSAN_STATS_OK")
