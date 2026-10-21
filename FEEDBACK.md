# Product feedback

Answers to the hackathon's product feedback questions, one section per tool.

> Lines marked **TODO** still need first-hand answers before submitting.

## Bee CLI (`@beeai/cli` 0.7.3, Windows 11)

**Which tools did you use and for what?**
`bee conversations list --json` to find recordings and `bee conversations get ID --json` to
fetch the transcript. The tool runs the CLI as a subprocess and parses the JSON.

**What worked well?**
- `--json` output is easy to consume from another program; no scraping of human-readable text.
- `npm install -g` puts a `bee.cmd` shim on `PATH` that Python's `shutil.which("bee")` finds,
  so the same subprocess code works on Windows and macOS/Linux.
- Utterances carry speaker labels and timestamps, which made evidence quotes possible.

**What needs work?**
- No documented JSON schema for `--json` responses (see FRICTION_LOG.md #3).
- `<id>` placeholders in docs break when pasted into PowerShell (#1).
- `bee now` uses a fixed 10-hour window that is not shown in its output (#2). I opened
  https://github.com/bee-computer/bee-cli/pull/27 to add `--hours N`.
- Recording boundaries are hard to predict: a recording sometimes ended on its own, one
  sentence landed outside its conversation, and a short recording disappeared (#6).

**Onboarding (zero to hello world)?** Smooth. Unlocking Developer Mode and `bee login` went
without problems, and the first `bee conversations list` worked right away.

## Bee app (as a user)

**What needs work?**
- **Privacy and control.** I am not comfortable wearing it in everyday life: it captures too
  much, and as a user I cannot predict what my recordings will become once they are collected
  and organised. If I only want to share the content of a meeting with someone, I first have to
  remove the fragments of my personal life from it.
- **Mixed-language interface.** With the app set to Chinese, the interface switches between
  Chinese and English. Even an all-English interface would be easier to use than the mix (#7).
- **Suggested to-dos are noisy.** Suggestions mostly point to Google Calendar and Gmail, even
  when the item was only a small part of a casual chat (#8).
- **Busy interface.** The overall interface feels cluttered and could be simpler.

**Would you build with it again?** Yes, for developer use and work conversations such as
meetings, where the tools here are smooth and useful. Not as an always-on device in daily life
until users get clearer control over what is captured, how it is processed and what is shared.

## DeepSeek API

**What for?** Turning a labelled transcript into structured issue drafts (JSON mode).

**What worked well?** JSON mode (`response_format: json_object`) returned parseable output on
every run so far; the 4 synthetic evaluation conversations scored precision 1.00 / recall 1.00.

**What needs work?** One transient network failure during evaluation; the tool now retries
network errors, 429 and 5xx responses. TODO: latency / cost observations.

**Would you use it again?** TODO

## GitHub REST API

**What for?** Creating issues, and listing existing issues for duplicate detection, using a
fine-grained token limited to "Issues: Read and write" on one repository.

**What needs work?** A token without access to a repository gets 404 instead of 403, which looks
like a typo in the repository name. The tool now explains this in its error message.

## Feature requests (optional)

| Request | Why it matters | Priority |
| --- | --- | --- |
| Share a single conversation (or a selected part) without the rest of my day, with easy redaction | Sharing meeting notes today means first deleting personal fragments | Critical |
| One integrations page listing all connected services; the user chooses which ones to use | To-do suggestions currently default to Google Calendar / Gmail even for casual remarks | Important |
| An assistant on the home screen that recommends the right integration from the user's description, and logs requests it cannot meet | Users find what they need faster, and unmet needs become a product backlog instead of being lost | Important |
| Consistent interface language (fully localised, or fully English) | Mixed Chinese/English UI is harder to read than either language alone | Important |
| JSON schema for every `bee ... --json` response | Integrations break silently when fields change | Important |
| Webhook or `bee conversations watch` for new conversations | Real-time workflows without polling | Important |
| Action items as structured JSON fields | Tools could build on Bee's own extraction | Nice-to-have |
| `--output FILE` (UTF-8) option | Avoids Windows PowerShell encoding pitfalls | Nice-to-have |
