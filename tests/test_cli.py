import json

from bee_issues import cli, github_client, llm

LLM_REPLY = json.dumps(
    {
        "issues": [
            {
                "title": "Fix login timeout when the token expires",
                "type": "bug",
                "summary": "Login page times out on staging.",
                "evidence": ["U1", "U2"],
                "confidence": 0.9,
            }
        ]
    }
)


def _draft(tmp_path, fixture_path, monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda system, user, settings: LLM_REPLY)
    code = cli.main([
        "--env-file", str(tmp_path / "missing.env"),
        "draft", "--input-json", str(fixture_path), "--out-dir", str(tmp_path),
    ])
    assert code == 0
    return tmp_path / "conversation-4242.json"


def test_draft_writes_file(tmp_path, fixture_path, monkeypatch, capsys):
    out = _draft(tmp_path, fixture_path, monkeypatch)
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["conversation"]["id"] == 4242
    issue = record["issues"][0]
    assert issue["github_labels"] == ["from-bee", "bug"]
    assert "The login page times out" in issue["body"]
    assert issue["published_url"] is None
    assert "Fix login timeout" in capsys.readouterr().out


def test_publish_dry_run_makes_no_calls(tmp_path, fixture_path, monkeypatch, capsys):
    out = _draft(tmp_path, fixture_path, monkeypatch)

    def fail(*args, **kwargs):
        raise AssertionError("no API calls in dry run")

    monkeypatch.setattr(github_client, "create_issue", fail)
    assert cli.main(["--env-file", "none", "publish", str(out), "--dry-run"]) == 0
    assert "(dry run)" in capsys.readouterr().out


def test_publish_records_url_and_skips_duplicates(tmp_path, fixture_path, monkeypatch, capsys):
    out = _draft(tmp_path, fixture_path, monkeypatch)
    monkeypatch.setenv("GITHUB_REPO", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    calls = []

    def fake_create(repo, token, title, body, labels):
        calls.append((repo, token, title, labels))
        return {"html_url": "https://github.com/o/r/issues/7"}

    monkeypatch.setattr(github_client, "create_issue", fake_create)
    monkeypatch.setattr(github_client, "list_issues", lambda repo, token: [])
    assert cli.main(["--env-file", "none", "publish", str(out), "--yes"]) == 0
    assert calls == [("o/r", "tok", "Fix login timeout when the token expires", ["from-bee", "bug"])]
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["issues"][0]["published_url"] == "https://github.com/o/r/issues/7"

    assert cli.main(["--env-file", "none", "publish", str(out), "--yes"]) == 0
    assert len(calls) == 1
    assert "already published" in capsys.readouterr().out


def test_publish_requires_repo(tmp_path, fixture_path, monkeypatch, capsys):
    out = _draft(tmp_path, fixture_path, monkeypatch)
    assert cli.main(["--env-file", "none", "publish", str(out), "--yes"]) == 1
    assert "GITHUB_REPO" in capsys.readouterr().err


def test_draft_requires_exactly_one_source(monkeypatch):
    import pytest

    with pytest.raises(SystemExit):
        cli.main(["--env-file", "none", "draft"])


def test_publish_skips_likely_duplicate_with_yes(tmp_path, fixture_path, monkeypatch, capsys):
    out = _draft(tmp_path, fixture_path, monkeypatch)
    monkeypatch.setenv("GITHUB_REPO", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    existing = [{"number": 3, "state": "open", "title": "Fix the login timeout when token expires",
                 "html_url": "https://github.com/o/r/issues/3"}]
    monkeypatch.setattr(github_client, "list_issues", lambda repo, token: existing)

    def fail(*args, **kwargs):
        raise AssertionError("duplicate must not be created")

    monkeypatch.setattr(github_client, "create_issue", fail)
    assert cli.main(["--env-file", "none", "publish", str(out), "--yes"]) == 0
    printed = capsys.readouterr().out
    assert "POSSIBLE DUPLICATE" in printed and "#3" in printed


def test_publish_no_dedup_skips_lookup(tmp_path, fixture_path, monkeypatch):
    out = _draft(tmp_path, fixture_path, monkeypatch)
    monkeypatch.setenv("GITHUB_REPO", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")

    def fail(*args, **kwargs):
        raise AssertionError("--no-dedup must not list issues")

    monkeypatch.setattr(github_client, "list_issues", fail)
    monkeypatch.setattr(github_client, "create_issue", lambda *a: {"html_url": "u"})
    assert cli.main(["--env-file", "none", "publish", str(out), "--yes", "--no-dedup"]) == 0


def test_transcript_prints_labels(fixture_path, capsys):
    assert cli.main(["--env-file", "none", "transcript", "--input-json", str(fixture_path)]) == 0
    printed = capsys.readouterr().out
    assert "U1 [speaker_1]: The login page times out" in printed


def test_eval_reports_precision_and_recall(tmp_path, fixture_path, monkeypatch, capsys):
    _draft(tmp_path, fixture_path, monkeypatch)
    expected = tmp_path / "4242.expected.json"
    expected.write_text(json.dumps({
        "conversation_id": 4242,
        "expected": [
            {"type": "bug", "keywords": ["login", "timeout"]},
            {"type": "feature", "keywords": ["csv", "export"]},
        ],
    }), encoding="utf-8")
    assert cli.main(["--env-file", "none", "eval", str(expected), "--drafts-dir", str(tmp_path)]) == 0
    printed = capsys.readouterr().out
    assert "MISSED keywords: csv, export" in printed
    assert "precision 1.00  recall 0.50" in printed


def test_watch_skips_existing_then_drafts_new_completed(tmp_path, fixture_path, monkeypatch, capsys):
    from bee_issues import bee_client

    conversation = bee_client.parse_conversation(json.loads(fixture_path.read_text(encoding="utf-8")))
    recent = [{"id": 1, "state": "COMPLETED", "start_time": 1}]
    fetched = []

    def fake_get(conversation_id, bee_bin=None):
        fetched.append(conversation_id)
        return conversation

    monkeypatch.setattr(bee_client, "list_conversations", lambda limit, bee_bin=None: list(recent))
    monkeypatch.setattr(bee_client, "get_conversation", fake_get)
    monkeypatch.setattr(llm, "complete", lambda system, user, settings: LLM_REPLY)
    watch = ["--env-file", "none", "watch", "--once", "--out-dir", str(tmp_path)]

    assert cli.main(watch) == 0  # first run: existing conversation 1 is skipped
    assert fetched == [] and "Skipping 1 existing" in capsys.readouterr().out

    recent.append({"id": 4242, "state": "CAPTURING", "start_time": 2})
    assert cli.main(watch) == 0  # not finished yet
    assert fetched == []

    recent[-1]["state"] = "COMPLETED"
    assert cli.main(watch) == 0
    assert fetched == [4242]
    assert (tmp_path / "conversation-4242.json").exists()
    assert "Fix login timeout" in capsys.readouterr().out

    assert cli.main(watch) == 0  # already handled
    assert fetched == [4242]
