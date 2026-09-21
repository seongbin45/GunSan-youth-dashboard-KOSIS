"""Agent state lives under data/agent_state/ (not project root)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent, AGENT_STATE_DIR, _safe_user_id


def test_safe_user_id_blocks_traversal():
    assert ".." not in _safe_user_id("../evil")
    assert "/" not in _safe_user_id("a/b")
    assert _safe_user_id("") == "default"


def test_persist_path_under_data_agent_state():
    a = FinFitAgent(user_id="path_probe_tmp")
    path = Path(a._get_persist_path())
    assert path.parent == AGENT_STATE_DIR
    assert path.name == "agent_state_path_probe_tmp.json"
    assert "data" in path.parts and "agent_state" in path.parts


def test_save_writes_only_to_data_dir(tmp_path=None):
    uid = "persist_write_tmp"
    a = FinFitAgent(user_id=uid)
    a.state.age = 33
    a.save()
    path = Path(a._get_persist_path())
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["state"]["age"] == 33
    # must not create new root file for this id (legacy may pre-exist from older runs)
    # After this test save, canonical is data/
    assert path.parent.resolve() == AGENT_STATE_DIR.resolve()


def test_legacy_root_migrates_on_load(tmp_path):
    """If only root legacy exists, load migrates copy into data/agent_state."""
    uid = "legacy_migrate_unit"
    safe = _safe_user_id(uid)
    legacy = ROOT / f"agent_state_{safe}.json"
    dest = AGENT_STATE_DIR / f"agent_state_{safe}.json"
    # clean
    if dest.is_file():
        dest.unlink()
    payload = {
        "state": {"age": 41, "level": None, "income_range": None, "first_goal": None,
                  "income_level": None, "employment_status": None, "has_house": None,
                  "monthly_income": None, "monthly_spend": None, "current_savings_rate": None,
                  "active_goals": [], "known_benefits": [], "last_updated": "t"},
        "memory": {"facts": [], "episodes": []},
    }
    legacy.write_text(json.dumps(payload), encoding="utf-8")
    try:
        a = FinFitAgent(user_id=uid)
        assert a.state.age == 41
        assert dest.is_file(), "migration should copy to data/agent_state"
    finally:
        if legacy.is_file():
            legacy.unlink()
        if dest.is_file():
            dest.unlink()
