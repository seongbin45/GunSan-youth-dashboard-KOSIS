"""Unit tests for KOSIS sync without live network."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.kosis_sync import (
    CORE_DATA_SPECS,
    DOMAIN_LIST_IDS,
    GUNSAN_YOUTH_ROOT_LIST_ID,
    sync_core_tables,
    needs_core_sync,
    last_core_sync_age_seconds,
    ensure_fresh_core,
    core_freshness_status,
)


class FakeClient:
    def fetch_list(self, parent_list_id, vw_cd="MT_ZTITLE"):
        return [
            {"LIST_NM": "dummy", "LIST_ID": parent_list_id, "VW_CD": vw_cd},
        ]

    def fetch_parameter_data(self, org_id, tbl_id, **kwargs):
        # minimal population-like rows
        return [
            {
                "C1_OBJ_NM": "지역별",
                "C2_NM": "청년인구(18~39세)",
                "DT": 56117,
                "C2": "B02",
                "C1": "A03",
                "PRD_DE": 2024,
                "C1_NM": "군산시",
                "UNIT_NM": "명",
                "TBL_ID": tbl_id,
                "ORG_ID": org_id,
                "TBL_NM": "test",
            }
        ]


def test_registry_matches_documentation():
    assert GUNSAN_YOUTH_ROOT_LIST_ID == "V_3_214_005"
    assert DOMAIN_LIST_IDS["population"] == "V_3_214_005_001"
    assert CORE_DATA_SPECS["gunsan_youth_population_success"]["tblId"] == "DT_712005_2024A001"
    assert CORE_DATA_SPECS["gunsan_youth_housing_data"]["tblId"] == "DT_712005_2024B001"
    assert CORE_DATA_SPECS["gunsan_youth_wage_data"]["tblId"] == "DT_712005_2024C005"


def test_sync_core_writes_tables(tmp_path):
    db = tmp_path / "t.db"
    result = sync_core_tables(client=FakeClient(), db_path=db)
    assert result["ok"] is True
    assert result["tables"]["gunsan_youth_population_success"]["rows"] == 1
    # readable by gunsan_stats
    from finfit_youth.gunsan_stats import get_gunsan_stat
    r = get_gunsan_stat("population", db_path=db)
    assert r.get("from_db") is True
    assert r["figures"]["gunsan_youth_18_39"] == 56117
    age = last_core_sync_age_seconds(db)
    assert age is not None and age < 5
    assert needs_core_sync(db, ttl=999999) is False


def test_ensure_fresh_skips_when_within_ttl(tmp_path, monkeypatch):
    db = tmp_path / "fresh.db"
    sync_core_tables(client=FakeClient(), db_path=db)
    monkeypatch.setenv("KOSIS_API_KEY", "dummy-key-for-test")
    # force config re-read is hard; pass client so no network and TTL huge
    out = ensure_fresh_core(db_path=db, ttl=999999, client=FakeClient())
    assert out.get("skipped") is True
    assert out.get("reason") == "within TTL"


def test_ensure_fresh_runs_when_stale(tmp_path, monkeypatch):
    db = tmp_path / "stale.db"
    # no prior sync → needs_core_sync True
    assert needs_core_sync(db, ttl=1) is True
    monkeypatch.setenv("KOSIS_API_KEY", "dummy-key-for-test")
    # ensure_fresh reads KOSIS_API_KEY from config module at call time
    import finfit_youth.config as cfg
    monkeypatch.setattr(cfg, "KOSIS_API_KEY", "dummy-key-for-test")
    out = ensure_fresh_core(db_path=db, ttl=1, client=FakeClient())
    assert out.get("skipped") is False
    assert out.get("ok") is True
    assert last_core_sync_age_seconds(db) is not None


def test_ensure_fresh_skips_without_key(tmp_path, monkeypatch):
    import finfit_youth.config as cfg

    monkeypatch.setattr(cfg, "KOSIS_API_KEY", "")
    out = ensure_fresh_core(db_path=tmp_path / "x.db", ttl=1, client=FakeClient())
    assert out.get("skipped") is True
    assert "KOSIS_API_KEY" in (out.get("reason") or "")


def test_core_freshness_status_readonly(tmp_path):
    db = tmp_path / "fs.db"
    # no sync yet
    st0 = core_freshness_status(db_path=db, ttl=100)
    assert st0["stale"] is True
    assert st0["age_seconds"] is None
    assert "summary" in st0
    sync_core_tables(client=FakeClient(), db_path=db)
    st1 = core_freshness_status(db_path=db, ttl=999999)
    assert st1["stale"] is False
    assert st1["age_seconds"] is not None
    assert st1["ttl_days"] >= 0


if __name__ == "__main__":
    test_registry_matches_documentation()
    import tempfile

    d = tempfile.mkdtemp()
    test_sync_core_writes_tables(Path(d))
    print("KOSIS_SYNC_OK")
