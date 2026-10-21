# Friction log

Moments where building with Bee slowed me down, in the order they happened.
Each entry uses the fields requested by the hackathon: task, steps, expected vs. actual,
severity, workaround and suggestion.

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
- **Suggestion / contribution:** I opened a pull request that adds `bee now --hours N` and
  prints "(none in the last N hours)", with tests:
  https://github.com/bee-computer/bee-cli/pull/27

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

## 5. Developer Mode / `bee login` (no friction)

- **Task:** Get from zero to the first `bee conversations list`.
- **Steps:** Unlocked Developer Mode in the Bee app, installed the CLI with npm, ran `bee login`.
- **Expected / Actual:** Worked as expected; the whole flow felt smooth.
- **Severity:** None. Recorded here as a positive data point.

## 6. Recording boundaries: one sentence moved, a short recording vanished

- **Task:** Record three short scripted notes (about 1 min, 1 min and 30 s) a couple of minutes apart.
- **Steps:** Recorded on 2026-10-21 around 10:14, 10:16 and 10:18, then polled
  `bee conversations list`.
- **Expected:** Three conversations. **Actual:** The first two appeared as `COMPLETED` within a
  few minutes and were correct, except that the last sentence of the second recording was not in
  its transcript. The third showed up as `CAPTURING` (id 11476962), and some minutes later it was
  gone from the list; `bee conversations get 11476962` returned "Conversation not found".
- **Severity:** Medium (silent data loss from the developer's point of view)
- **Workaround:** Re-recorded with about a minute of speech (read twice); it became one
  conversation (id 11477324) and was `COMPLETED` about 6 minutes after recording started. In
  normal use, recordings also sometimes ended on their own before I had finished.
- **Suggestion:** Document the minimum length / discard rules, and expose a `DISCARDED` state
  (or an event in `bee changed` / `bee stream`) instead of the conversation disappearing.

## 7. Mixed-language app interface

- **Task:** Use the Bee app with the interface set to Chinese.
- **Steps:** Browsed conversations, summaries and suggestions in the app.
- **Expected:** One consistent language. **Actual:** The interface switches between Chinese and English.
- **Severity:** Medium (affects every screen)
- **Workaround:** None.
- **Suggestion:** Localise fully, or fall back to all-English rather than mixing per string.

## 8. Suggested to-dos point to Google Calendar and Gmail

- **Task:** Review the to-dos Bee suggested after everyday conversations.
- **Steps:** Opened the suggested to-do list in the app.
- **Expected:** A few relevant suggestions. **Actual:** A cluttered list where most items link
  to Google Calendar or Gmail, even when the source was a minor remark in casual chat.
- **Severity:** Medium
- **Workaround:** Ignored the list.
- **Suggestion:** Let users choose which integrations to use from one page, and raise the bar
  for turning casual remarks into suggestions.

## 9. Sharing a meeting means removing my private life first

- **Task:** Share what was said in a meeting with someone else.
- **Steps:** Looked at what the recordings and summaries contained.
- **Expected:** Share only the meeting. **Actual:** Personal fragments of my day are mixed in,
  and I cannot predict how collected data will be organised later, so I would have to remove
  them myself before sharing.
- **Severity:** High for everyday use (main reason I would not wear it all day)
- **Workaround:** Only record deliberately, for work.
- **Suggestion:** Per-conversation sharing with redaction, and a clear view of what is
  captured and how it will be used.
