#!/usr/bin/env bash
# Set up agent-skills on this machine. Safe to re-run (it updates).
#   curl -fsSL https://raw.githubusercontent.com/georgejpeters/agent-skills/main/install.sh | bash
#   or: git clone https://github.com/georgejpeters/agent-skills ~/.agent-skills && ~/.agent-skills/install.sh
#
# 1. Clones (or pulls) the repo into $AGENT_SKILLS_DIR (default ~/.agent-skills).
# 2. Claude Code: registers it as a plugin marketplace and installs every plugin in it.
# 3. Imports AGENTS.md into ~/.claude/CLAUDE.md (one marked line; your own rules are kept).
# 4. Codex: links ~/.codex/AGENTS.md to it if you have no AGENTS.md there yet.
# Plugins to install can be narrowed: AGENT_SKILLS_PLUGINS="guardrails quant" ./install.sh
set -euo pipefail
REPO_URL=${AGENT_SKILLS_REPO:-https://github.com/georgejpeters/agent-skills}
DIR=${AGENT_SKILLS_DIR:-$HOME/.agent-skills}
MARKER="# agent-skills (managed by install.sh)"

if [[ -d $DIR/.git ]]; then
  git -C "$DIR" pull -q --ff-only || { echo "git pull failed in $DIR" >&2; exit 1; }
  echo "updated $DIR"
else
  git clone -q "$REPO_URL" "$DIR" || { echo "git clone of $REPO_URL failed" >&2; exit 1; }
  echo "cloned into $DIR"
fi

plugins=${AGENT_SKILLS_PLUGINS:-$(cd "$DIR/plugins" && ls)}

if command -v claude >/dev/null; then
  if claude plugin marketplace list 2>/dev/null | grep -q 'agent-skills'; then
    claude plugin marketplace update agent-skills >/dev/null && echo "marketplace refreshed"
  else
    claude plugin marketplace add "$DIR" >/dev/null && echo "marketplace added"
  fi
  for p in $plugins; do
    if claude plugin install "$p@agent-skills" >/dev/null 2>&1; then echo "installed $p"; else echo "$p: already installed (or failed: run 'claude plugin install $p@agent-skills')"; fi
  done
  mkdir -p "$HOME/.claude"
  touch "$HOME/.claude/CLAUDE.md"
  if ! grep -qF "$MARKER" "$HOME/.claude/CLAUDE.md"; then
    printf '\n%s\n@%s/AGENTS.md\n' "$MARKER" "$DIR" >> "$HOME/.claude/CLAUDE.md"
    echo "imported AGENTS.md into ~/.claude/CLAUDE.md"
  fi
else
  echo "Claude Code not found: skipped plugins (install it, then re-run)."
fi

if [[ -d $HOME/.codex && ! -e $HOME/.codex/AGENTS.md ]]; then
  ln -s "$DIR/AGENTS.md" "$HOME/.codex/AGENTS.md" && echo "linked ~/.codex/AGENTS.md"
fi

echo "done. Start a new session to load the plugins. Update later by re-running this script."
