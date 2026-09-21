# ceo skill

Makes AI agents reply like they are briefing a time-poor CEO: answer first, fewest words, one recommendation, one clear ask. It picks the reply shape by response type (BLUF, answer-first SCQA, 1-3-1, What / So what / Now what, RYG) and never cuts risk, errors, or skipped scope for brevity.

One folder works on Claude Code, Codex CLI (GPT), and Z.ai ZCode (GLM), which all read the Agent Skills `SKILL.md` format.

## Install

```bash
./install.sh
```

This copies the skill to `~/.claude/skills/ceo` and `~/.agents/skills/ceo`. ZCode reads `~/.agents/skills` itself.

## Use

| Where | Type this |
|---|---|
| Claude Code | `/ceo` then your message, or say "ceo mode" |
| Codex CLI | `$ceo` then your message, or say "ceo mode" |
| ZCode | `$ceo` then your message, or say "ceo mode" |
| ChatGPT, claude.ai, other chat apps | See `adapters/chat-paste-block.md` |

Say "ceo off" to turn it off. To make it the default in every session, paste the block from `adapters/always-on-snippet.md` into your `CLAUDE.md` or `AGENTS.md`.

## What is inside

- `SKILL.md`: 12 response types, each with a shape, a tag, and a word cap, plus the cut check and the never-cut check.
- `references/examples.md`: an example reply for each type.
- `references/frameworks.md`: when each framework fits and misfits.
- `adapters/`: the always-on snippet and paste blocks for chat apps.
- `evals/`: 10 scenarios and `run.py`, which runs them on the `claude`, `codex`, and ZCode CLIs and checks caps, tags, and banned phrases.

## Test results

With the skill invoked by name, on 10 scenarios plus a 3-turn persistence test (one or two runs each, so indicative only): Claude 8 of 10, GPT 10 of 10, GLM 10 of 10, and all three stayed in CEO mode across 3 turns. Without the skill the same prompts ran up to 717 words.

## License

MIT
