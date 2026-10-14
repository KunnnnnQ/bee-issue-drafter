# Product feedback

Feedback on the tools used to build bee-issue-drafter, for the
*Build, Ship, Shape: Amazon Developer Hackathon* submission.

> Lines marked **TODO** still need to be written from first-hand experience before submitting.

## Bee CLI (`@beeai/cli`, tested with 0.7.3 on Windows 11)

**What I used it for.** Listing conversations (`bee conversations list --json`) and fetching a
full conversation with its transcript (`bee conversations get <id> --json`). The tool calls the
CLI as a subprocess and parses the JSON.

**What worked well.**
- `--json` output is easy to consume from another program; no scraping of human-readable text.
- Installing through npm puts a `bee.cmd` shim on `PATH`, and Python's `shutil.which("bee")`
  finds it on Windows, so the same subprocess code works on Windows and macOS/Linux.
- Bee's own conversation summaries already include an "Action Items" section. That made it clear
  that this project has to go further: technical classification, issue formatting, evidence
  quotes and duplicate checks.

**Problems / suggestions.**
- Docs use `<id>` placeholders. In PowerShell `<` is a reserved operator, so copying the example
  literally gives a parser error instead of a helpful message. Using `ID` or `12345` in examples
  would avoid this.
- `bee now` only covers roughly the last 10 hours; when it returns nothing it is not obvious
  whether that means "no recordings" or "not logged in". A one-line hint would help.
- The JSON shape of `conversations get` is not documented as a schema; I read the CLI source to
  find `transcriptions[].utterances[]` and the `realtime` flag. A published schema would help.
- TODO: anything about Developer Mode unlock, `bee login`, sync delay after recording.

**Would I use it again?** TODO

## Claude API (Anthropic) / Claude on Amazon Bedrock

**What I used it for.** Turning a labelled transcript into structured issue drafts (JSON).

- TODO: which provider and model you actually used, latency, cost, JSON reliability.

## GitHub REST API

**What I used it for.** Creating issues and listing existing issues for duplicate detection,
with a fine-grained personal access token limited to "Issues: Read and write" on one repository.

- TODO: setup experience.

## AWS services

TODO: only if Bedrock or another AWS service was used. Otherwise delete this section.
