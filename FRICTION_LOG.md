# Friction log

Moments where building with Bee slowed me down, in the order they happened.
Format: what I tried → what happened → what I expected → suggestion.

> Add an entry every time something blocks you for more than a few minutes. Entries marked
> **TODO** are placeholders.

| # | Date | Area | What happened | Expected | Suggestion |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-10 | Bee CLI docs | Copied `bee conversations get <id> --json` into PowerShell; got a parser error because `<` is reserved. | Example runs after replacing the id. | Use `12345` or `ID` in examples instead of `<id>`. |
| 2 | 2026-10 | Bee CLI | `bee now` printed nothing. Had to work out that it only covers about the last 10 hours. | A message such as "no conversations in the last 10 hours". | Print an explicit empty-state message. |
| 3 | TODO verify | Windows | Saving CLI output with `>` in Windows PowerShell 5.1 writes UTF-16, which then fails to parse as UTF-8 JSON in Python. Workaround: `Out-File -Encoding utf8`. | Plain UTF-8 file. | Mention the encoding in the docs, or add an `--output FILE` option to the CLI. |
| 4 | 2026-10 | Bee data | Bee summaries already contain "Action Items", so a naive "extract todos" tool would add nothing. | — | (Design note, not a bug.) |
| 5 | TODO | Developer Mode / login | TODO | | |
| 6 | TODO | Sync delay | TODO: how long between finishing a recording and it appearing in `bee conversations list`? | | |
