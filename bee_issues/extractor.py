"""Turn a Bee conversation transcript into GitHub issue drafts with an LLM.

The model only returns structured fields plus the labels of the transcript
lines it relied on (e.g. "U3"). Evidence quotes in the issue body are copied
from the real transcript, not written by the model.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Callable

from bee_issues.bee_client import Conversation

MAX_TRANSCRIPT_CHARS = 60_000
ISSUE_TYPES = ("bug", "feature", "task", "question")

SYSTEM_PROMPT = """You turn transcripts of technical discussions into GitHub issue drafts.
The transcript was recorded by a wearable device (Bee) and is automatic speech recognition output:
it may contain recognition errors, overlapping speakers and off-topic chatter.

Rules:
- Only create an issue for a concrete, actionable technical item: a bug, a feature request,
  a task, or an open technical question that needs follow-up.
- Ignore personal, social or non-technical content entirely.
- Do not invent facts that the transcript does not support. If something is unclear,
  say so in "details" instead of guessing.
- Every issue must cite the transcript lines it is based on, by their labels (e.g. "U3").
- One issue per distinct problem or task; merge duplicates.
- If there is nothing actionable, return {"issues": []}.

Respond with JSON only, no prose and no code fences, in exactly this shape:
{"issues": [{"title": "short imperative title",
             "type": "bug | feature | task | question",
             "summary": "1-2 sentences",
             "details": "what was said, context, open points",
             "acceptance_criteria": ["..."],
             "labels": ["..."],
             "evidence": ["U3", "U4"],
             "confidence": 0.0}]}"""


class ExtractionError(ValueError):
    pass


@dataclass
class IssueDraft:
    title: str
    type: str = "task"
    summary: str = ""
    details: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def build_user_prompt(conversation: Conversation) -> str:
    summary = (conversation.summary or "").strip() or "(none)"
    transcript = conversation.transcript_text(max_chars=MAX_TRANSCRIPT_CHARS) or "(empty)"
    return (
        f"Bee conversation #{conversation.id}\n"
        f"Bee's own summary (may be incomplete): {summary}\n\n"
        f"Transcript lines:\n{transcript}"
    )


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ExtractionError(f"Model reply contains no JSON object: {text[:200]!r}")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Model reply is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ExtractionError("Model reply JSON must be an object.")
    return data


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def parse_drafts(reply: str, valid_refs: set[str]) -> tuple[list[IssueDraft], list[str]]:
    """Validate the model's JSON. Returns (drafts, warnings)."""
    data = _extract_json_object(reply)
    items = data.get("issues")
    if not isinstance(items, list):
        raise ExtractionError('Model reply JSON has no "issues" list.')

    drafts: list[IssueDraft] = []
    warnings: list[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not str(item.get("title") or "").strip():
            warnings.append(f"Skipped item {index}: missing title.")
            continue
        issue_type = str(item.get("type") or "task").strip().lower()
        if issue_type not in ISSUE_TYPES:
            issue_type = "task"
        evidence = _str_list(item.get("evidence"))
        unknown = [ref for ref in evidence if ref not in valid_refs]
        if unknown:
            warnings.append(f"Item {index}: dropped unknown evidence refs {unknown}.")
        evidence = [ref for ref in evidence if ref in valid_refs]
        if not evidence:
            warnings.append(f"Item {index} ({item['title']!r}) has no valid evidence; review it carefully.")
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence") or 0.0)))
        except (TypeError, ValueError):
            confidence = 0.0
        drafts.append(
            IssueDraft(
                title=str(item["title"]).strip()[:200],
                type=issue_type,
                summary=str(item.get("summary") or "").strip(),
                details=str(item.get("details") or "").strip(),
                acceptance_criteria=_str_list(item.get("acceptance_criteria")),
                labels=_str_list(item.get("labels")),
                evidence=evidence,
                confidence=confidence,
            )
        )
    return drafts, warnings


def extract_drafts(
    conversation: Conversation, complete: Callable[[str, str], str]
) -> tuple[list[IssueDraft], list[str]]:
    """Ask the LLM (via `complete(system, user)`) for issue drafts."""
    if not conversation.utterances:
        return [], [f"Conversation {conversation.id} has no transcript utterances."]
    reply = complete(SYSTEM_PROMPT, build_user_prompt(conversation))
    valid_refs = set(conversation.utterance_by_ref())
    return parse_drafts(reply, valid_refs)


def issue_labels(draft: IssueDraft, max_labels: int = 5) -> list[str]:
    labels: list[str] = []
    for label in ["from-bee", draft.type, *draft.labels]:
        label = label.strip().lower()
        if label and label not in labels:
            labels.append(label)
    return labels[:max_labels]


def render_issue_body(draft: IssueDraft, conversation: Conversation) -> str:
    parts: list[str] = []
    if draft.summary:
        parts += ["## Summary", draft.summary, ""]
    if draft.details:
        parts += ["## Details", draft.details, ""]
    if draft.acceptance_criteria:
        parts.append("## Acceptance criteria")
        parts += [f"- [ ] {item}" for item in draft.acceptance_criteria]
        parts.append("")
    by_ref = conversation.utterance_by_ref()
    quotes = [by_ref[ref] for ref in draft.evidence if ref in by_ref]
    if quotes:
        parts.append(f"## Evidence (Bee conversation #{conversation.id})")
        for u in quotes:
            when = f" ({u.time_label()})" if u.time_label() else ""
            parts.append(f"> **{u.speaker}**{when}: {u.text}")
            parts.append(">")
        parts.pop()
        parts += ["", "_Quotes are automatic speech recognition output and may contain errors._", ""]
    parts += [
        "---",
        f"_Drafted by bee-issue-drafter from Bee conversation #{conversation.id} "
        f"(model confidence {draft.confidence:.2f})._",
    ]
    return "\n".join(parts)
