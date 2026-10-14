import json

import pytest

from bee_issues.bee_client import parse_conversation
from bee_issues.extractor import (
    ExtractionError,
    IssueDraft,
    extract_drafts,
    issue_labels,
    parse_drafts,
    render_issue_body,
)

REPLY = {
    "issues": [
        {
            "title": "Fix login timeout when the token expires",
            "type": "bug",
            "summary": "Login page spins and times out after 30s on staging.",
            "details": "Seen every time the token expires.",
            "acceptance_criteria": ["Expired token redirects to login within 2s"],
            "labels": ["auth", "Bug"],
            "evidence": ["U1", "U2", "U99"],
            "confidence": 0.8,
        },
        {"title": "", "type": "task"},
        {"title": "Add CSV export to reports", "type": "enhancement", "evidence": [], "confidence": "high"},
    ]
}


def test_parse_drafts_validates_items():
    text = "```json\n" + json.dumps(REPLY) + "\n```"
    drafts, warnings = parse_drafts(text, {"U1", "U2", "U3"})
    assert [d.title for d in drafts] == [
        "Fix login timeout when the token expires",
        "Add CSV export to reports",
    ]
    assert drafts[0].evidence == ["U1", "U2"]
    assert drafts[1].type == "task"  # unknown type falls back to task
    assert drafts[1].confidence == 0.0  # non-numeric confidence
    assert any("U99" in w for w in warnings)
    assert any("missing title" in w for w in warnings)
    assert any("no valid evidence" in w for w in warnings)


@pytest.mark.parametrize("reply", ["no json here", '{"issues": "nope"}', "{broken"])
def test_parse_drafts_rejects_bad_replies(reply):
    with pytest.raises(ExtractionError):
        parse_drafts(reply, set())


def test_extract_drafts_sends_transcript_to_llm(conversation_payload):
    conv = parse_conversation(conversation_payload)
    seen = {}

    def fake_complete(system, user):
        seen["system"], seen["user"] = system, user
        return json.dumps(REPLY)

    drafts, _ = extract_drafts(conv, fake_complete)
    assert "Respond with JSON only" in seen["system"]
    assert "U1 [speaker_1]: The login page times out" in seen["user"]
    assert "Bee conversation #4242" in seen["user"]
    assert len(drafts) == 2


def test_empty_conversation_skips_llm():
    conv = parse_conversation({"conversation": {"id": 1, "transcriptions": []}})

    def boom(system, user):
        raise AssertionError("LLM should not be called")

    drafts, warnings = extract_drafts(conv, boom)
    assert drafts == [] and warnings


def test_render_body_quotes_real_transcript(conversation_payload):
    conv = parse_conversation(conversation_payload)
    draft = IssueDraft(
        title="Fix login timeout",
        type="bug",
        summary="Login times out.",
        acceptance_criteria=["Works"],
        labels=["Auth"],
        evidence=["U2"],
        confidence=0.75,
    )
    body = render_issue_body(draft, conv)
    assert "## Evidence (Bee conversation #4242)" in body
    assert "> **speaker_2**" in body and "the page just spins" in body
    assert "- [ ] Works" in body
    assert "confidence 0.75" in body
    assert issue_labels(draft) == ["from-bee", "bug", "auth"]
