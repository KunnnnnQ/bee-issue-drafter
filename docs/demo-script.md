# Demo video script (target 2:45, English)

Rules from the hackathon: under 3 minutes, public on YouTube or Vimeo, best content first.
Show real Bee data, but only a recording made for the demo (your own voice, no other people).

| Time | Screen | Say |
| --- | --- | --- |
| 0:00–0:15 | Bee on wrist, then a GitHub issues page full of `from-bee` issues | "Bugs and decisions come up when we talk, and they get lost. bee-issue-drafter turns what my Bee heard into reviewable GitHub issues." |
| 0:15–0:45 | You talk while coding for ~20 s (cut down); include one bug, one TODO, one open question and one off-topic line | (the recording itself) |
| 0:45–1:00 | Terminal: `python -m bee_issues list --limit 3` | "The recording synced through the Bee app. The tool reads it with the official Bee CLI in JSON mode." |
| 1:00–1:40 | `python -m bee_issues draft <id>`; scroll through 2 drafts | "The model only returns structure and the line labels it relied on. The quotes are copied from the real transcript, so it cannot invent evidence. Notice the off-topic sentence was ignored." |
| 1:40–2:05 | `publish` → answer `y` → open the created issue in the browser | "Nothing is posted until I confirm each issue." |
| 2:05–2:25 | Run `publish` again on a re-drafted file → `POSSIBLE DUPLICATE ... #1` | "It checks existing issues first, so repeating the same bug in tomorrow's stand-up does not create a duplicate." |
| 2:25–2:40 | `eval` output with precision / recall | "Every prompt change is measured against hand-written expected issues, including chit-chat that must produce nothing." |
| 2:40–2:45 | Repo URL | "Open source, MIT licensed. Thanks!" |

Recording tips:
- Increase the terminal font size (Ctrl + mouse wheel) before recording.
- Do one take of the live recording in advance so the sync delay does not show in the video.
- Before uploading, check that no token, API key or other person's speech is visible.
