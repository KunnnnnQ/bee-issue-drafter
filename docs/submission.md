# Devpost submission draft

> Copy into the Devpost form. Lines marked **TODO** need your input before submitting.

**Track:** Bee (Wearable AI), priority use case: developer experience / personal productivity.
Fits the judging examples "ambient context capture that informs a productivity workflow".

**Mini challenge:** Open Source. Required fields:
- Contribution URL: https://github.com/bee-computer/bee-cli/pull/27 — adds `bee now --hours N`
  and a clearer empty state, with tests; found while building this project (FRICTION_LOG #2).
  Fork: https://github.com/KunnnnnQ/bee-cli/tree/feat/now-hours-window
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
- **`watch` mode** drafts issues automatically for each new finished Bee conversation.
- 36 unit tests that make no network calls; CI on Windows and Ubuntu.

## Challenges

- **Unpredictable recording boundaries.** One sentence landed outside its conversation, and a
  30-second recording showed up as `CAPTURING` and then disappeared. Longer recordings worked.
  This also exposed a bug in my own `watch` mode (started mid-recording, it skipped that
  recording), which I fixed with a test.
- **Privacy.** Bee records everything, including other people and my private life. The
  repository only contains synthetic data; real transcripts stay in git-ignored folders, and the
  tool only processes conversations the user picks.
- **The Bee JSON shape is undocumented**, so I read the bee-cli source to parse transcripts.

## Accomplishments

- End-to-end on a real Bee device: on three scripted recordings, every technical item in the
  transcripts was found (10 of 10) with no extra issues; chit-chat, remarks about the recording
  and already-finished work were ignored.
- The first real run produced one false positive ("quick test for the demo" became a task).
  The `eval` command caught it, a one-line prompt rule fixed it, and the synthetic set confirmed
  nothing else got worse.
- Contributed back to Bee: https://github.com/bee-computer/bee-cli/pull/27 (`bee now --hours`).

## What we learned

- Bee's own summaries already list action items, so the value is in what comes after:
  structure, evidence, and fitting into the developer's existing tracker without duplicates.
- With speech input, measuring beats guessing: small hand-written expected lists were enough to
  find and fix a real prompt problem.
- For an always-on wearable, user control over what is captured and shared matters as much as
  the AI features.

## What's next

- Use `bee stream` instead of polling so drafts appear as soon as a conversation ends.
- Route issues to the right repository when one person works on several projects.
- Assign issues based on who spoke (speaker identification).

## Built with

python, bee-cli, deepseek, github-api, github-actions

## Links

- Repository: https://github.com/KunnnnnQ/bee-issue-drafter
- Video: https://youtu.be/SyOC9ALOYgs
- Product feedback: see FEEDBACK.md and FRICTION_LOG.md in the repository
