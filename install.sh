#!/usr/bin/env bash
# Copies the ceo skill into the skill folders for Claude Code, Codex CLI, and ZCode (GLM).
# ZCode reads ~/.agents/skills itself (checked with `zcode skills list`), so a copy in
# ~/.zcode/skills would list the skill twice.
# Copies instead of symlinking so the install survives this repo moving.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=(
  "$HOME/.claude/skills/ceo"
  "$HOME/.agents/skills/ceo"
)

for dest in "${TARGETS[@]}"; do
  mkdir -p "$dest"
  cp -R "$SRC/SKILL.md" "$SRC/references" "$dest/"
  echo "Installed: $dest"
done

echo "For always-on use, see adapters/always-on-snippet.md. For chat apps, see adapters/chat-paste-block.md."
