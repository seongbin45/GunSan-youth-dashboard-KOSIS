"""Turn log schema + redaction + append (temp path)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.turn_log import (
    SCHEMA_VERSION,
    build_turn_record,
    append_turn_log,
    log_agent_turn,
    turn_log_enabled,
)
from finfit_youth.agent import FinFitAgent
from finfit_youth.tools import execute_tool_dict


def test_build_record_shape():
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    steps = [
        {
            "tool": "get_gunsan_youth_stats",
            "input": {"category": "population"},
            "output": out,
        }
    ]
    plan = {
        "steps": [
            {
                "tool": "get_gunsan_youth_stats",
                "args": {"category": "population"},
            }
        ],
        "clarify": False,
    }
    rec = build_turn_record(
        query="군산시 청년 인구 현황 어때?",
        plan=plan,
        tool_steps=steps,
        answer="인구는 약 56,117명입니다. " + ("충분 " * 20),
        assumptions=[{"field": "age", "value": 25, "reason": "test"}],
        guard={"ok": True, "unmatched": []},
        mode="test",
        depth="shallow",
    )
    assert rec["schema"] == SCHEMA_VERSION
    assert rec["query"].startswith("군산")
    assert rec["plan"]["tools"] == ["get_gunsan_youth_stats"]
    assert rec["plan"]["categories"] == ["population"]
    assert rec["external_tool_count"] == 1
    assert rec["tools"][0]["tool"] == "get_gunsan_youth_stats"
    assert "args_digest" in rec["tools"][0]
    assert rec["figures_digest"]  # grounded numbers
    assert rec["assumptions"][0]["field"] == "age"
    assert rec["guard"]["ok"] is True
    assert rec["answer_chars"] > 0
    assert len(rec["answer_excerpt"]) <= 400


def test_redact_api_key_like_tokens():
    rec = build_turn_record(
        query="my key sk-abcdefghijklmnopqrstuvwxyz123456",
        plan={},
        tool_steps=[],
        answer="secret api_key=supersecretvalue123",
    )
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in rec["query"]
    assert "supersecretvalue123" not in rec["answer_excerpt"]
    assert "REDACTED" in rec["query"] or "REDACTED" in rec["answer_excerpt"]


def test_append_jsonl(tmp_path):
    path = tmp_path / "turns.jsonl"
    rec = build_turn_record(query="hello", plan={"clarify": True, "steps": []}, answer="hi")
    written = append_turn_log(rec, path=path, enabled=True)
    assert written == path
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["query"] == "hello"
    assert loaded["plan"]["clarify"] is True


def test_append_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("FINFIT_TURN_LOG", "0")
    assert turn_log_enabled() is False
    path = tmp_path / "off.jsonl"
    rec = build_turn_record(query="x", answer="y")
    assert append_turn_log(rec, path=path, enabled=None) is None
    assert not path.exists()


def test_log_agent_turn_with_guard(tmp_path):
    a = FinFitAgent(user_id="turnlog")
    a.clear_turn_scratch()
    out = execute_tool_dict("get_gunsan_youth_stats", {"category": "population"})
    steps = [{"tool": "get_gunsan_youth_stats", "input": {"category": "population"}, "output": out}]
    # force guard path via synthesize
    a.synthesize_final(
        "인구 999999명이라고 합니다. " + ("본문 " * 30),
        steps,
        "군산시 청년 인구 현황 어때?",
    )
    path = tmp_path / "agent.jsonl"
    written = log_agent_turn(
        query="군산시 청년 인구 현황 어때?",
        plan={
            "steps": [
                {"tool": "get_gunsan_youth_stats", "args": {"category": "population"}}
            ],
            "clarify": False,
        },
        tool_steps=steps,
        answer=a.synthesize_final(
            "인구 약 56117명. " + ("ok " * 20),
            steps,
            "군산시 청년 인구 현황 어때?",
        ),
        agent=a,
        mode="test",
        path=path,
        enabled=True,
    )
    assert written == path
    row = json.loads(path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["user_id"] == "turnlog"
    assert "figures_digest" in row
