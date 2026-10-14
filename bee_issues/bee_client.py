"""Thin wrapper around the official Bee CLI (`npm install -g @beeai/cli`).

We call the CLI with `--json` and parse its output. The JSON shapes follow the
bee-cli source code (sources/resources/conversations/index.ts):

- `bee conversations list --json`
    -> {"conversations": [{"id", "start_time", "end_time", "summary", ...}],
        "next_cursor": ..., "timezone": ...}
- `bee conversations get <id> --json`
    -> {"conversation": {"id", "start_time", "summary", ...,
                         "transcriptions": [{"realtime": bool,
                                             "utterances": [{"id", "speaker", "text",
                                                             "spoken_at", "start", ...}]}]},
        "timezone": ...}
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

TRUNCATION_NOTE = "[... transcript truncated ...]"


class BeeCliError(RuntimeError):
    """Raised when the Bee CLI is missing, fails, or returns unexpected output."""


@dataclass
class Utterance:
    ref: str  # label used in the LLM prompt and as evidence, e.g. "U3"
    speaker: str
    text: str
    timestamp_ms: int | None = None

    def time_label(self) -> str:
        return format_epoch_ms(self.timestamp_ms)


@dataclass
class Conversation:
    id: int
    start_time_ms: int | None = None
    summary: str | None = None
    timezone: str | None = None
    utterances: list[Utterance] = field(default_factory=list)

    def utterance_by_ref(self) -> dict[str, Utterance]:
        return {u.ref: u for u in self.utterances}

    def transcript_text(self, max_chars: int | None = None) -> str:
        lines: list[str] = []
        used = 0
        for u in self.utterances:
            line = f"{u.ref} [{u.speaker}]: {u.text}"
            if max_chars is not None and used + len(line) + 1 > max_chars:
                lines.append(TRUNCATION_NOTE)
                break
            lines.append(line)
            used += len(line) + 1
        return "\n".join(lines)


def format_epoch_ms(value: int | None) -> str:
    """Format an epoch-milliseconds timestamp in local time; empty if unknown."""
    if not isinstance(value, (int, float)) or value < 1_000_000_000_000:
        return ""
    return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d %H:%M")


def find_bee(bee_bin: str | None = None) -> str:
    if bee_bin:
        return bee_bin
    path = shutil.which("bee")
    if not path:
        raise BeeCliError(
            "Bee CLI not found on PATH. Install it with `npm install -g @beeai/cli`, "
            "then run `bee login`. You can also set BEE_BIN in .env to the full path."
        )
    return path


def run_bee(args: list[str], bee_bin: str | None = None, timeout: int = 60) -> Any:
    """Run `bee <args>` and return parsed JSON from stdout."""
    exe = find_bee(bee_bin)
    command = "bee " + " ".join(args)
    try:
        result = subprocess.run(
            [exe, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise BeeCliError(f"`{command}` timed out after {timeout}s") from exc
    except OSError as exc:
        raise BeeCliError(f"Could not run `{command}`: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise BeeCliError(
            f"`{command}` failed (exit {result.returncode}): {detail}\n"
            "If you are not logged in, run `bee login` first."
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BeeCliError(f"`{command}` did not return JSON: {result.stdout[:200]!r}") from exc


def bee_version(bee_bin: str | None = None) -> Any:
    return run_bee(["version", "--json"], bee_bin)


def list_conversations(limit: int = 10, bee_bin: str | None = None) -> list[dict]:
    payload = run_bee(["conversations", "list", "--limit", str(limit), "--json"], bee_bin)
    if not isinstance(payload, dict) or not isinstance(payload.get("conversations"), list):
        raise BeeCliError("Unexpected response from `bee conversations list --json`.")
    return payload["conversations"]


def get_conversation(conversation_id: int, bee_bin: str | None = None) -> Conversation:
    payload = run_bee(["conversations", "get", str(conversation_id), "--json"], bee_bin)
    return parse_conversation(payload)


def _number(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def parse_conversation(payload: Any) -> Conversation:
    """Convert `bee conversations get --json` output into a Conversation."""
    if not isinstance(payload, dict):
        raise BeeCliError("Conversation JSON must be an object.")
    conv = payload.get("conversation", payload)
    if not isinstance(conv, dict) or _number(conv.get("id")) is None:
        raise BeeCliError("Conversation JSON has no numeric `id`.")

    transcriptions = [t for t in (conv.get("transcriptions") or []) if isinstance(t, dict)]
    # Same choice as bee-cli: prefer the non-realtime (final) transcription.
    chosen = next((t for t in transcriptions if not t.get("realtime")), None)
    if chosen is None and transcriptions:
        chosen = transcriptions[0]
    raw = [u for u in ((chosen or {}).get("utterances") or []) if isinstance(u, dict)]

    def sort_key(u: dict) -> tuple[int, int]:
        ts = _number(u.get("spoken_at"))
        if ts is None:
            ts = _number(u.get("start"))
        return (ts or 0, _number(u.get("id")) or 0)

    utterances: list[Utterance] = []
    for u in sorted(raw, key=sort_key):
        text = str(u.get("text") or "").strip()
        if not text:
            continue
        ts = _number(u.get("spoken_at"))
        if ts is None:
            ts = _number(u.get("start"))
        utterances.append(
            Utterance(
                ref=f"U{len(utterances) + 1}",
                speaker=str(u.get("speaker") or "unknown"),
                text=text,
                timestamp_ms=ts,
            )
        )

    timezone = payload.get("timezone") if isinstance(payload.get("timezone"), str) else None
    summary = conv.get("summary") if isinstance(conv.get("summary"), str) else None
    return Conversation(
        id=int(conv["id"]),
        start_time_ms=_number(conv.get("start_time")),
        summary=summary,
        timezone=timezone,
        utterances=utterances,
    )
