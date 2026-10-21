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
- `bee now` prints nothing when there is no data (#2).
- TODO: anything else you hit.

**Onboarding (zero to hello world)?** TODO: Developer Mode unlock, `bee login`, time to the
first `bee conversations list`.

**Would you build with it again?** TODO: Yes/No and why.

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
| JSON schema for every `bee ... --json` response | Integrations break silently when fields change | Important |
| Webhook or `bee conversations watch` for new conversations | Real-time workflows without polling | Important |
| Action items as structured JSON fields | Tools could build on Bee's own extraction | Nice-to-have |
| `--output FILE` (UTF-8) option | Avoids Windows PowerShell encoding pitfalls | Nice-to-have |
