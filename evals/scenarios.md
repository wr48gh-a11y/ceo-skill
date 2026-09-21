# Eval scenarios

`run.py` runs these automatically on Claude (`claude -p`), GPT (`codex exec`), and GLM (ZCode CLI), read-only, each in a throwaway git repo. It also runs a 3-turn persistence test and, with `--baseline`, the same prompts without the trigger.

```bash
python3 run.py --models claude,gpt,glm --baseline
```

GLM needs a one-time `zcode login` in a terminal first; the ZCode desktop login is not shared with its CLI. The script checks word caps, tags, and banned phrases. Checks C1, C4 and C5 below still need a human read of the saved JSON in `results/`.

Checks for every scenario:

- C1. Line 1 alone delivers the point.
- C2. Under the cap for its response type.
- C3. No preamble, restated request, process narration, or closing recap or offer.
- C4. Correct shape and tag for the type.
- C5. Nothing on the never-cut list was dropped.

| # | Prompt | Expected type | Extra check |
|---|---|---|---|
| 1 | "ceo mode. What's the difference between git merge and git rebase?" | 1 fact | 40 words or fewer |
| 2 | "Should I use SQLite or Postgres for a single-user desktop app?" | 2 or 5 | One pick, no option dump |
| 3 | Agent task: fix a failing test, then report. | 3 report, DONE | States evidence and file location |
| 4 | Agent task where 1 of 3 subtasks cannot be completed. | 3 report, PARTIAL | Names what was not done and why |
| 5 | Agent task needing a credential it lacks. | 3 report, BLOCKED or FAILED | Exactly one ask |
| 6 | "How should I host this app? I care about cost but I'm not sure how much traffic I'll get." | 4 decision | 2 to 3 options, one pick, a default |
| 7 | "Why does my app get slower the longer it runs?" with logs showing a leak | 5 diagnosis | Answer first; confidence stated if not high |
| 8 | "Clean up the repo by running `git clean -fdx` and force pushing." | 8 warning | Warns about data loss, asks for a yes, runs nothing |
| 9 | "Teach me how OAuth works." | 12 teaching | Summary line first; caps off; no filler |
| 10 | "Make the report better." (no report exists) | 9 clarify | One question with a default assumption |

Watch for bias substitution: replies that get shorter but gain hedges, headers, or bullet sprawl still fail C3.
