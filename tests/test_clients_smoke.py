"""Tests sans réseau du wrapper forge.clients."""

import json
import os

import pytest

import forge.clients as clients
from forge.clients import MissingAPIKeyError, complete

MSGS = [{"role": "user", "content": "Dis « bonjour » en un mot."}]


@pytest.fixture
def tmp_log(tmp_path, monkeypatch):
    p = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FORGE_LOG_PATH", str(p))
    return p


def test_import():
    assert callable(complete)


def test_complete_logs_jsonl(tmp_log, monkeypatch):
    fake = {"text": "Bonjour", "in_tokens": 12, "out_tokens": 2, "model_resolved": "fake"}
    monkeypatch.setattr(clients, "_dispatch", lambda model, messages, **kw: fake)

    r = complete("fake/model", MSGS, temperature=0)

    assert r["text"] == "Bonjour" and r["in_tokens"] == 12 and r["out_tokens"] == 2
    lines = tmp_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "« bonjour »" in lines[0]  # ensure_ascii=False
    rec = json.loads(lines[0])
    assert rec["model"] == "fake/model"
    assert rec["output"] == "Bonjour"
    assert rec["meta"] == {"temperature": 0}
    assert len(rec["prompt_hash"]) == 10


def test_missing_key_raises_clear_error(tmp_log, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        complete("gpt-4o-mini", MSGS)
    rec = json.loads(tmp_log.read_text(encoding="utf-8").splitlines()[-1])
    assert "MissingAPIKeyError" in rec["error"]


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY absent")
def test_live_openrouter(tmp_log):
    r = complete("openrouter/openai/gpt-4o-mini", MSGS, max_tokens=10)
    assert r["text"]
