# Devpost submission draft

> Copy into the Devpost form. Lines marked **TODO** need your input before submitting.

**Track:** Bee (Wearable AI), priority use case: developer experience / personal productivity.
Fits the judging examples "ambient context capture that informs a productivity workflow".

**Mini challenge:** Open Source. Required fields:
- Contribution URL: TODO: bee-cli pull request URL (branch:
  https://github.com/KunnnnnQ/bee-cli/tree/feat/now-hours-window — adds `bee now --hours N`
  and a clearer empty state, with tests; found while building this project, see FRICTION_LOG #2)
- Project repository URL: https://github.com/KunnnnnQ/bee-issue-drafter
- GitHub username: KunnnnnQ
- What / how / why: new MIT-licensed tool created during the hackathon; Bee CLI → LLM with
  grounded evidence → duplicate-checked GitHub issues; evaluation command and tests so other
  developers can extend it safely.

**New & existing:** The project was created during the Submission Period (first commit 2026-10-14).

**Bee runtime requirement:** `bee_issues/bee_client.py` runs the Bee CLI at runtime
(`bee conversations list/get --json`); the demo uses a real recording from a Bee device.

## Inspiration

Bugs, decisions and open questions come up in conversation: stand-ups, pair debugging,
thinking aloud while coding. Most of them never reach the issue tracker. Bee already records
these conversations and even lists action items, but a developer needs more than a to-do line:
a typed, well-formed issue in the right repository, with evidence, that is not a duplicate of
one that already exists.

## What it does

bee-issue-drafter reads a conversation recorded by Bee and drafts GitHub issues from the
technical parts only:

- classifies each item as bug, feature, task or question, with summary, details and
  acceptance criteria;
- quotes the exact transcript lines it relied on as evidence;
- ignores personal and off-topic speech;
- checks existing open and closed issues and flags likely duplicates;
- creates nothing until the user confirms each issue.

## How we built it

- **Bee CLI** (`@beeai/cli`) in `--json` mode to list conversations and fetch transcripts.
- **Python** command-line tool (`python -m bee_issues`), standard library plus `requests`.
- **LLM** behind a small provider interface: DeepSeek, Claude API or Claude on Amazon Bedrock.
  The model sees transcript lines labelled `U1, U2, ...` and must answer in JSON with those
  labels as evidence. Quotes in the issue body are copied from the real transcript, and unknown
  labels are dropped, so the model cannot invent quotes.
- **GitHub REST API** with a fine-grained token limited to Issues on one repository.
- **Evaluation:** an `eval` command scores drafts against hand-written expected issues
  (precision, recall, type accuracy), including hard synthetic cases such as speech recognition
  errors, pure chit-chat and repeated mentions.
- 30+ unit tests that make no network calls; CI on Windows and Ubuntu.

## Challenges

TODO: from your own experience. Candidates: Windows specifics (PowerShell `<id>` and encoding),
understanding the Bee JSON shape, keeping personal recordings out of a public repository.

## Accomplishments

TODO: your results on real Bee recordings (precision / recall from `eval`).

## What we learned

TODO

## What's next

- Run continuously: watch for new Bee conversations and draft automatically.
- Route issues to the right repository when one person works on several projects.
- Assign issues based on who spoke (speaker identification).

## Built with

python, bee-cli, deepseek, github-api, github-actions

## Links

- Repository: https://github.com/KunnnnnQ/bee-issue-drafter
- Video: TODO
- Product feedback: see FEEDBACK.md and FRICTION_LOG.md in the repository
