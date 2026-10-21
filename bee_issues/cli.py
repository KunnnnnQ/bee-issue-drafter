"""Command-line entry point: python -m bee_issues <command>."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bee_issues import __version__, bee_client, github_client, llm
from bee_issues.bee_client import BeeCliError, Conversation, format_epoch_ms
from bee_issues.config import Settings, load_settings
from bee_issues.evaluate import describe, evaluate
from bee_issues.extractor import ExtractionError, extract_drafts, issue_labels, render_issue_body
from bee_issues.github_client import GitHubError
from bee_issues.llm import LLMError
from bee_issues.matching import find_duplicate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bee_issues",
        description="Turn technical discussions recorded by Bee into GitHub issue drafts.",
    )
    parser.add_argument("--env-file", default=".env", help="path to the .env file (default: .env)")
    parser.add_argument("--version", action="version", version=f"bee-issue-drafter {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="check the Bee CLI and show which settings are configured")

    p_list = sub.add_parser("list", help="list recent Bee conversations")
    p_list.add_argument("--limit", type=int, default=10)

    def add_source(p: argparse.ArgumentParser) -> None:
        p.add_argument("conversation_id", nargs="?", type=int, help="Bee conversation id (see `list`)")
        p.add_argument("--latest", action="store_true", help="use the most recent conversation")
        p.add_argument(
            "--input-json",
            help="read saved `bee conversations get <id> --json` output from a file",
        )

    p_show = sub.add_parser("transcript", help="print a conversation with its U1, U2, ... line labels")
    add_source(p_show)

    p_draft = sub.add_parser("draft", help="draft GitHub issues from one Bee conversation")
    add_source(p_draft)
    p_draft.add_argument("--out-dir", default="drafts", help="where to save drafts (default: drafts)")

    p_watch = sub.add_parser(
        "watch", help="keep checking Bee and draft issues for each new finished conversation"
    )
    p_watch.add_argument("--interval", type=int, default=60, help="seconds between checks (default: 60)")
    p_watch.add_argument("--limit", type=int, default=10, help="recent conversations to check (default: 10)")
    p_watch.add_argument("--out-dir", default="drafts", help="where to save drafts (default: drafts)")
    p_watch.add_argument("--once", action="store_true", help="check once and exit")

    p_pub = sub.add_parser("publish", help="create GitHub issues from a drafts file")
    p_pub.add_argument("drafts_file")
    p_pub.add_argument("--only", help="comma-separated issue numbers to publish, e.g. 1,3")
    p_pub.add_argument("--yes", action="store_true", help="do not ask before creating each issue")
    p_pub.add_argument("--dry-run", action="store_true", help="show what would be created; no API calls")
    p_pub.add_argument(
        "--no-dedup", action="store_true", help="do not compare with issues already in the repo"
    )

    p_eval = sub.add_parser("eval", help="compare drafts with hand-written expected issues")
    p_eval.add_argument("expected_files", nargs="+", help="expected-issues JSON file(s)")
    p_eval.add_argument("--drafts-dir", default="drafts", help="where drafts are saved (default: drafts)")
    return parser


def cmd_check(settings: Settings) -> int:
    ok = True
    print("Bee CLI")
    try:
        print(f"  path:    {bee_client.find_bee(settings.bee_bin)}")
        print(f"  version: {json.dumps(bee_client.bee_version(settings.bee_bin), ensure_ascii=False)}")
        print("  tip:     run `bee status` to confirm you are logged in")
    except BeeCliError as exc:
        print(f"  ERROR: {exc}")
        ok = False
    print("\nSettings (.env)")
    for key, value in settings.status().items():
        print(f"  {key}: {value}")
    if settings.github_repo and settings.github_token:
        print("\nGitHub")
        try:
            repo = github_client.get_repo(settings.github_repo, settings.github_token)
            print(f"  repo:    {repo.get('html_url')} (issues enabled: {repo.get('has_issues')})")
        except GitHubError as exc:
            print(f"  ERROR: {exc}")
            ok = False
    return 0 if ok else 1


def cmd_list(settings: Settings, limit: int) -> int:
    conversations = bee_client.list_conversations(limit=limit, bee_bin=settings.bee_bin)
    if not conversations:
        print("No conversations found.")
        return 0
    for conv in conversations:
        summary = " ".join(str(conv.get("summary") or "").split())
        if len(summary) > 90:
            summary = summary[:87] + "..."
        started = format_epoch_ms(conv.get("start_time")) or "?"
        print(f"{conv.get('id'):>10}  {started:16}  {summary or '(no summary yet)'}")
    return 0


def _load_conversation(args: argparse.Namespace, settings: Settings) -> Conversation:
    chosen = [args.conversation_id is not None, args.latest, args.input_json is not None]
    if sum(chosen) != 1:
        raise SystemExit(f"{args.command}: give exactly one of CONVERSATION_ID, --latest or --input-json")
    if args.input_json:
        payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        return bee_client.parse_conversation(payload)
    conversation_id = args.conversation_id
    if args.latest:
        recent = bee_client.list_conversations(limit=1, bee_bin=settings.bee_bin)
        if not recent:
            raise BeeCliError("No Bee conversations found.")
        conversation_id = int(recent[0]["id"])
    return bee_client.get_conversation(conversation_id, bee_bin=settings.bee_bin)


def cmd_transcript(args: argparse.Namespace, settings: Settings) -> int:
    conversation = _load_conversation(args, settings)
    print(f"Conversation #{conversation.id}: {len(conversation.utterances)} utterances")
    print(conversation.transcript_text())
    return 0


def _draft_and_save(
    conversation: Conversation, settings: Settings, out_dir: str
) -> tuple[Path, list[dict], list[str]]:
    drafts, warnings = extract_drafts(
        conversation, lambda system, user: llm.complete(system, user, settings)
    )
    issues = []
    for draft in drafts:
        item = draft.to_dict()
        item["github_labels"] = issue_labels(draft)
        item["body"] = render_issue_body(draft, conversation)
        item["published_url"] = None
        issues.append(item)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    out_file = out_path / f"conversation-{conversation.id}.json"
    record = {
        "tool": f"bee-issue-drafter {__version__}",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "llm": {"provider": settings.llm_provider, "model": llm.model_name(settings)},
        "conversation": {
            "id": conversation.id,
            "start_time_ms": conversation.start_time_ms,
            "summary": conversation.summary,
        },
        "warnings": warnings,
        "issues": issues,
    }
    out_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_file, issues, warnings


def cmd_draft(args: argparse.Namespace, settings: Settings) -> int:
    conversation = _load_conversation(args, settings)
    print(f"Conversation #{conversation.id}: {len(conversation.utterances)} utterances")
    out_file, issues, warnings = _draft_and_save(conversation, settings, args.out_dir)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if not issues:
        print("No actionable technical items found.")
    for number, item in enumerate(issues, start=1):
        print("\n" + "=" * 72)
        print(f"[{number}] {item['title']}")
        print(f"labels: {', '.join(item['github_labels'])}   confidence: {item['confidence']:.2f}")
        print("-" * 72)
        print(item["body"])
    print(f"\nSaved {len(issues)} draft(s) to {out_file}")
    if issues:
        print(f"Review or edit that file, then run: python -m bee_issues publish {out_file}")
    return 0


def _load_seen(path: Path) -> set[int] | None:
    if not path.exists():
        return None
    return {int(x) for x in json.loads(path.read_text(encoding="utf-8")).get("seen", [])}


def _save_seen(path: Path, seen: set[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"seen": sorted(seen)}), encoding="utf-8")


def _watch_once(args: argparse.Namespace, settings: Settings, state_file: Path) -> None:
    recent = bee_client.list_conversations(limit=args.limit, bee_bin=settings.bee_bin)
    seen = _load_seen(state_file)
    if seen is None:
        # First run: only conversations recorded from now on are drafted.
        seen = {int(c["id"]) for c in recent}
        _save_seen(state_file, seen)
        print(f"Watching Bee. Skipping {len(seen)} existing conversation(s); new ones will be drafted.")
        return
    for conv in sorted(recent, key=lambda c: c.get("start_time") or 0):
        conversation_id = int(conv["id"])
        if conversation_id in seen or conv.get("state") != "COMPLETED":
            continue  # still being captured or processed by Bee; check again next time
        conversation = bee_client.get_conversation(conversation_id, bee_bin=settings.bee_bin)
        if not conversation.utterances:
            continue  # transcript not synced yet
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{stamp}] New conversation #{conversation_id} ({len(conversation.utterances)} utterances)")
        out_file, issues, warnings = _draft_and_save(conversation, settings, args.out_dir)
        for warning in warnings:
            print(f"  WARNING: {warning}")
        for number, item in enumerate(issues, start=1):
            print(f"  [{number}] ({item['type']}) {item['title']}")
        if issues:
            print(f"  Review, then run: python -m bee_issues publish {out_file}")
        else:
            print("  No actionable technical items.")
        seen.add(conversation_id)
        _save_seen(state_file, seen)


def cmd_watch(args: argparse.Namespace, settings: Settings) -> int:
    state_file = Path(args.out_dir) / ".watch-state.json"
    try:
        while True:
            try:
                _watch_once(args, settings, state_file)
            except (BeeCliError, LLMError, ExtractionError) as exc:
                if args.once:
                    raise
                print(f"Error (will retry): {exc}", file=sys.stderr)
            if args.once:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


def _parse_only(value: str | None, total: int) -> list[int]:
    if not value:
        return list(range(1, total + 1))
    numbers = []
    for part in value.split(","):
        part = part.strip()
        if not part.isdigit() or not 1 <= int(part) <= total:
            raise SystemExit(f"--only: {part!r} is not an issue number between 1 and {total}")
        numbers.append(int(part))
    return numbers


def cmd_publish(args: argparse.Namespace, settings: Settings) -> int:
    path = Path(args.drafts_file)
    record = json.loads(path.read_text(encoding="utf-8"))
    issues = record.get("issues") or []
    if not issues:
        print("Nothing to publish.")
        return 0
    if not args.dry_run and not settings.github_repo:
        raise GitHubError("GITHUB_REPO is not set. Add it to your .env file.")

    existing: list[dict] = []
    if not args.dry_run and not args.no_dedup:
        existing = github_client.list_issues(settings.github_repo, settings.github_token or "")
        print(f"Loaded {len(existing)} existing issue(s) from {settings.github_repo} for duplicate check.")

    created = 0
    for number in _parse_only(args.only, len(issues)):
        item = issues[number - 1]
        if item.get("published_url"):
            print(f"[{number}] already published: {item['published_url']}")
            continue
        title, body, labels = item["title"], item["body"], item.get("github_labels") or []
        print("\n" + "=" * 72)
        print(f"[{number}] {title}\nlabels: {', '.join(labels)}")
        if args.dry_run:
            print("-" * 72 + "\n" + body)
            print(f"(dry run) would create this issue in {settings.github_repo or 'GITHUB_REPO'}")
            continue
        duplicate = find_duplicate(title, existing)
        if duplicate:
            match, score = duplicate
            print(
                f"POSSIBLE DUPLICATE ({score:.0%} similar) of #{match.get('number')} "
                f"[{match.get('state')}]: {match.get('title')}\n  {match.get('html_url')}"
            )
            if args.yes:
                print("skipped (use --no-dedup to create it anyway)")
                continue
        if not args.yes:
            answer = input(f"Create this issue in {settings.github_repo}? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("skipped")
                continue
        result = github_client.create_issue(
            settings.github_repo, settings.github_token or "", title, body, labels
        )
        item["published_url"] = result.get("html_url")
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        created += 1
        existing.append(result)
        print(f"created: {item['published_url']}")
    if not args.dry_run:
        print(f"\nCreated {created} issue(s).")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    totals = {"matched": 0, "missed": 0, "extra": 0}
    for expected_file in args.expected_files:
        spec = json.loads(Path(expected_file).read_text(encoding="utf-8"))
        conversation_id = spec.get("conversation_id")
        drafts_file = Path(args.drafts_dir) / f"conversation-{conversation_id}.json"
        if not drafts_file.exists():
            print(f"{expected_file}: no drafts file {drafts_file}; run `draft` first")
            return 1
        drafts = json.loads(drafts_file.read_text(encoding="utf-8")).get("issues") or []
        result = evaluate(drafts, spec.get("expected") or [], conversation_id)
        print(f"\n== Conversation #{conversation_id} ({expected_file})")
        for exp, got in result.matched:
            type_note = "" if not exp.get("type") or exp["type"] == got.get("type") else (
                f"  [type: expected {exp['type']}, got {got.get('type')}]"
            )
            print(f"  OK     {describe(exp)}  ->  {got.get('title')}{type_note}")
        for exp in result.missed:
            print(f"  MISSED {describe(exp)}")
        for got in result.extra:
            print(f"  EXTRA  {got.get('title')}")
        print(
            f"  precision {result.precision:.2f}  recall {result.recall:.2f}  "
            f"type accuracy {result.type_accuracy:.2f}"
        )
        totals["matched"] += len(result.matched)
        totals["missed"] += len(result.missed)
        totals["extra"] += len(result.extra)
    if len(args.expected_files) > 1:
        found = totals["matched"] + totals["extra"]
        wanted = totals["matched"] + totals["missed"]
        print(
            f"\nOverall: precision {totals['matched'] / found if found else 1:.2f}  "
            f"recall {totals['matched'] / wanted if wanted else 1:.2f}  "
            f"({totals['matched']} matched, {totals['missed']} missed, {totals['extra']} extra)"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")  # avoid crashes on non-UTF-8 consoles
    args = build_parser().parse_args(argv)
    settings = load_settings(args.env_file)
    try:
        if args.command == "check":
            return cmd_check(settings)
        if args.command == "list":
            return cmd_list(settings, args.limit)
        if args.command == "transcript":
            return cmd_transcript(args, settings)
        if args.command == "draft":
            return cmd_draft(args, settings)
        if args.command == "watch":
            return cmd_watch(args, settings)
        if args.command == "publish":
            return cmd_publish(args, settings)
        if args.command == "eval":
            return cmd_eval(args)
    except (BeeCliError, LLMError, ExtractionError, GitHubError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 2
