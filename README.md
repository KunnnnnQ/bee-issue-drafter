# bee-issue-drafter

Turn technical discussions recorded by a [Bee](https://bee.computer) wearable into
reviewable GitHub issue drafts.

Built for the **Bee (Wearable AI)** track of *Build, Ship, Shape: Amazon Developer Hackathon*.

## The problem

Bugs, feature ideas and follow-up tasks often come up in spoken discussions
(stand-ups, pair debugging, hallway chats). They get lost because nobody writes them down.

## How it works

```
Bee device / Apple Watch
        |  (Bee app syncs the recording)
        v
Bee CLI  -- bee conversations get <id> --json -->  transcript (utterances U1, U2, ...)
        |
        v
LLM (Claude API or Claude on Amazon Bedrock)
        |  returns structured JSON: title, type, summary, acceptance criteria,
        |  and the transcript line labels it used as evidence
        v
drafts/conversation-<id>.json   <-- you review / edit this file
        |
        v
python -m bee_issues publish    -- checks for duplicates, asks before each issue --> GitHub Issues
```

Design choices:

- **Human in the loop.** Nothing is posted to GitHub until you confirm each issue.
- **Grounded evidence.** The model only returns line labels such as `U3`. The quotes in the
  issue body are copied from the real Bee transcript, so the model cannot invent quotes.
  Unknown labels are dropped and reported as warnings.
- **No duplicate spam.** Before publishing, existing open and closed issues in the repo are
  loaded and similar titles are flagged. With `--yes`, likely duplicates are skipped.
- **Measurable.** `eval` compares drafts with a hand-written list of expected issues and reports
  precision and recall, so prompt changes can be checked instead of guessed.
- **Plain CLI.** It uses the official Bee CLI with `--json`, which Bee recommends for
  automation.

## Requirements

- Python 3.10+
- Node.js (for the Bee CLI)
- A Bee account with Developer Mode unlocked in the Bee iOS app
  (see the [Bee developer docs](https://docs.bee.computer/docs))
- One LLM option: a Claude API key, **or** AWS credentials with access to Claude on Amazon Bedrock
- For publishing: a GitHub fine-grained personal access token

## Setup (Windows PowerShell)

```powershell
# 1. Bee CLI
npm install -g @beeai/cli
bee login
bee status

# 2. Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# only if you use Amazon Bedrock:
pip install boto3

# 3. Configuration
copy .env.example .env
notepad .env
```

macOS / Linux: use `python3 -m venv .venv`, `source .venv/bin/activate` and `cp .env.example .env`.

## Configuration (`.env`)

| Variable | Needed for | Description |
| --- | --- | --- |
| `LLM_PROVIDER` | `draft` | `anthropic` (default) or `bedrock` |
| `ANTHROPIC_API_KEY` | `draft` with `anthropic` | Claude API key |
| `ANTHROPIC_MODEL` | `draft` with `anthropic` | Default `claude-sonnet-5-5` |
| `AWS_REGION`, `BEDROCK_MODEL_ID` | `draft` with `bedrock` | Region and model id. Check the exact id (or inference profile id) in your Bedrock console |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `draft` with `bedrock` | Optional if you already ran `aws configure` |
| `GITHUB_TOKEN` | `publish` | Fine-grained token with **Issues: Read and write** on the target repo |
| `GITHUB_REPO` | `publish` | Target repository as `owner/name` |
| `BEE_BIN` | optional | Full path to `bee` if it is not on `PATH` |

`.env` is listed in `.gitignore`. Never commit it.

## Try it without a Bee device

`examples/sample_conversation.json` is a hand-written sample in the same shape as
`bee conversations get <id> --json`. You only need an LLM key from the setup above.

```powershell
python -m bee_issues transcript --input-json examples\sample_conversation.json
python -m bee_issues draft --input-json examples\sample_conversation.json
python -m bee_issues eval examples\sample_conversation.expected.json
python -m bee_issues publish drafts\conversation-1001.json --dry-run
```

## Usage

```powershell
python -m bee_issues check                 # Bee CLI found? settings set? GitHub token works?
python -m bee_issues list --limit 10       # recent Bee conversations
python -m bee_issues transcript 12345      # transcript with the U1, U2, ... labels
python -m bee_issues draft 12345           # draft issues from conversation 12345
python -m bee_issues draft --latest        # ... or from the newest conversation
python -m bee_issues publish drafts\conversation-12345.json --dry-run
python -m bee_issues publish drafts\conversation-12345.json            # asks y/N per issue
python -m bee_issues publish drafts\conversation-12345.json --only 1,3
python -m bee_issues publish drafts\conversation-12345.json --no-dedup  # skip the duplicate check
```

You can edit the title, body or labels in the drafts JSON file before publishing.
Published issues get their URL saved in the file, so running `publish` twice does not
create duplicates.

## Evaluating the drafts

Write down what a good run should produce for a conversation, then compare:

```json
{"conversation_id": 12345,
 "expected": [
   {"type": "bug", "keywords": ["login", "email"]},
   {"type": "question", "title": "Decide the upload size limit"}
 ]}
```

```powershell
python -m bee_issues draft 12345
python -m bee_issues eval data\eval\12345.expected.json   # several files give an overall score
```

A draft matches an expected item when all keywords appear in its title, summary or details
(or, without keywords, when the titles are similar). Each side is matched at most once.
Unmatched drafts count as false positives, for example chit-chat turned into an issue.
Keep expected files for real recordings under `data/`, which is git-ignored.

## Privacy

- Bee transcripts are personal data and may include other people's voices.
  `drafts/`, `bee-sync/` and `data/` are git-ignored. The only conversation data in this
  repository is synthetic (`examples/`, `tests/fixtures/`).
- Published issue bodies contain short transcript quotes as evidence. Check them before you
  confirm, especially for public repositories.
- The transcript is sent to the LLM provider you configure.

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

The tests use a hand-written synthetic conversation (`tests/fixtures/synthetic_conversation.json`)
and fake LLM / GitHub clients. They make no network calls.

## Project status

Early MVP. Covered by unit tests with synthetic data; not yet run end-to-end against live
Bee data. `--input-json` is for offline development and for trying the tool without a device.

Product feedback and a friction log for the hackathon are in [FEEDBACK.md](FEEDBACK.md) and
[FRICTION_LOG.md](FRICTION_LOG.md).

## License

MIT, see [LICENSE](LICENSE).
