# Friction log

Moments where building with Bee slowed me down, in the order they happened.
Each entry uses the fields requested by the hackathon: task, steps, expected vs. actual,
severity, workaround and suggestion.

> Entries marked **TODO** still need first-hand details before submitting.

## 1. Fetching one conversation from PowerShell

- **Task:** Export one conversation as JSON on Windows.
- **Steps:** Copied `bee conversations get <id> --json` from the docs into PowerShell and replaced nothing.
- **Expected:** A hint that `<id>` must be replaced. **Actual:** PowerShell parser error, because `<` is a reserved operator.
- **Severity:** Low
- **Workaround:** Type the numeric id without angle brackets.
- **Suggestion:** Use a concrete example such as `bee conversations get 12345 --json` in the docs.

## 2. `bee now` has a fixed, unstated time window

- **Task:** Check that recent recordings are available.
- **Steps:** Ran `bee now` after a period without recording.
- **Expected:** To see my latest recordings, or be told which time range was searched. **Actual:** Only "- (none)"; the 10-hour window is hard-coded and only mentioned in the README.
- **Severity:** Low
- **Workaround:** Used `bee conversations list --limit 3` instead.
- **Suggestion / contribution:** I opened a change that adds `bee now --hours N` and prints
  "(none in the last N hours)", with tests:
  https://github.com/KunnnnnQ/bee-cli/tree/feat/now-hours-window

## 3. Finding the JSON shape of a conversation

- **Task:** Parse `bee conversations get --json` in Python.
- **Steps:** Looked for a schema in the docs; ended up reading the bee-cli source to find `transcriptions[].utterances[]` and the `realtime` flag.
- **Expected:** A documented response schema. **Actual:** Shape only discoverable from source or by inspecting output.
- **Severity:** Medium
- **Workaround:** Read `sources/resources/conversations` in the bee-cli repository.
- **Suggestion:** Publish a JSON schema or a typed example response for each `--json` command.

## 4. Bee summaries already contain action items

- **Task:** Decide what the project adds beyond Bee itself.
- **Steps:** Read the summaries of my own conversations.
- **Expected / Actual:** Bee already lists "Action Items", so a plain to-do extractor would add nothing.
- **Severity:** Design note
- **Workaround:** Focused on what Bee does not do: technical classification, issue format, evidence quotes, duplicate checks against an existing repository.
- **Suggestion:** Expose action items as structured fields in `--json` so tools can build on them directly.

## 5. TODO: Developer Mode / `bee login`

- **Task:** Get from zero to the first `bee conversations list`.
- **Steps:** TODO
- **Expected / Actual:** TODO
- **Severity:** TODO
- **Workaround:** TODO
- **Suggestion:** TODO

## 6. Recording boundaries: one sentence moved, a short recording vanished

- **Task:** Record three short scripted notes (about 1 min, 1 min and 30 s) a couple of minutes apart.
- **Steps:** Recorded on 2026-10-21 around 10:14, 10:16 and 10:18, then polled
  `bee conversations list`.
- **Expected:** Three conversations. **Actual:** The first two appeared as `COMPLETED` within a
  few minutes and were correct, except that the last sentence of the second recording was not in
  its transcript. The third showed up as `CAPTURING` (id 11476962), and some minutes later it was
  gone from the list; `bee conversations get 11476962` returned "Conversation not found".
- **Severity:** Medium (silent data loss from the developer's point of view)
- **Workaround:** Re-record with longer speech. TODO: note the result.
- **Suggestion:** Document the minimum length / discard rules, and expose a `DISCARDED` state
  (or an event in `bee changed` / `bee stream`) instead of the conversation disappearing.
