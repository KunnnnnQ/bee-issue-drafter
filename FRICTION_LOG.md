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

## 2. Empty output from `bee now`

- **Task:** Check that recent recordings are available.
- **Steps:** Ran `bee now` after a period without recording.
- **Expected:** A message such as "no conversations in the last 10 hours". **Actual:** No output at all, so it was unclear whether I was logged out or simply had no data.
- **Severity:** Low
- **Workaround:** Used `bee conversations list --limit 3` instead.
- **Suggestion:** Print an explicit empty-state message.

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

## 6. TODO: Sync delay after recording

- **Task:** Draft issues right after a recording.
- **Steps:** Recorded, then ran `bee conversations list`.
- **Expected / Actual:** TODO: how many minutes until the conversation and its transcript appeared?
- **Severity:** TODO
- **Workaround:** TODO
- **Suggestion:** TODO
