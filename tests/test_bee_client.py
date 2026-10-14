import subprocess

import pytest

from bee_issues import bee_client
from bee_issues.bee_client import BeeCliError, parse_conversation


def test_parse_prefers_final_transcription_sorts_and_skips_empty(conversation_payload):
    conv = parse_conversation(conversation_payload)
    assert conv.id == 4242
    assert conv.timezone == "Asia/Hong_Kong"
    assert [u.ref for u in conv.utterances] == ["U1", "U2", "U3", "U4"]
    assert conv.utterances[0].text.startswith("The login page times out")
    assert all("realtime draft" not in u.text for u in conv.utterances)
    assert conv.utterances[1].speaker == "speaker_2"


def test_transcript_text_and_truncation(conversation_payload):
    conv = parse_conversation(conversation_payload)
    full = conv.transcript_text()
    assert full.splitlines()[0] == (
        "U1 [speaker_1]: The login page times out after thirty seconds on the staging server."
    )
    short = conv.transcript_text(max_chars=100)
    assert short.endswith(bee_client.TRUNCATION_NOTE)
    assert len(short.splitlines()) == 2


def test_parse_rejects_missing_id():
    with pytest.raises(BeeCliError):
        parse_conversation({"conversation": {"summary": "x"}})


def test_run_bee_parses_json(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout='{"conversations": [{"id": 1}]}', stderr="")

    monkeypatch.setattr(bee_client.shutil, "which", lambda name: "/usr/bin/bee")
    monkeypatch.setattr(bee_client.subprocess, "run", fake_run)
    assert bee_client.list_conversations(limit=3) == [{"id": 1}]
    assert calls[0] == ["/usr/bin/bee", "conversations", "list", "--limit", "3", "--json"]


def test_run_bee_reports_failure(monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Not logged in")

    monkeypatch.setattr(bee_client.subprocess, "run", fake_run)
    with pytest.raises(BeeCliError, match="Not logged in"):
        bee_client.run_bee(["me", "--json"], bee_bin="/opt/bee")


def test_missing_bee_cli(monkeypatch):
    monkeypatch.setattr(bee_client.shutil, "which", lambda name: None)
    with pytest.raises(BeeCliError, match="npm install -g @beeai/cli"):
        bee_client.find_bee()
