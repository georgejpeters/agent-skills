# Working agreements for AI coding agents

Portable rules for any coding agent (Claude Code, Codex, Cursor, Copilot…). On a new machine,
`install.sh` imports this file into Claude Code's global `~/.claude/CLAUDE.md`. Other tools can
read it as `AGENTS.md` directly.

## Never block on long work

- Anything that could take more than ~30 seconds runs in the background: remote jobs over ssh,
  scans, backtests, training, backfills, builds, package installs, bulk copies. Write to a log.
- Remote jobs run detached (`setsid nohup … > log 2>&1 < /dev/null &`) so they survive a dropped
  connection. Wait for them in the background, not in a foreground loop.
- While it runs, keep talking: say **what is running, where the log is, and the ETA**.
- Needing a longer timeout is the signal that something belongs in the background.

## Never expose secrets

- Never print `.env` files, keys, tokens, decrypted secrets or password-manager items into the
  conversation. List key names (`cut -d= -f1 .env`), test values (`grep -q '^KEY=' .env`), edit
  in place (`sed -i`).
- Never commit secrets. Machine-local config stays out of git and gets documented instead.
- Repositories are private unless the owner explicitly says otherwise.

## Evidence over confidence

- Test before claiming. Report results with their uncertainty, and report failures plainly with
  the output.
- When a number looks too good, look for the artefact first: leakage, look-ahead, a definition
  mismatch, survivorship, an unrealistic fill.
- Time-ordered data gets time-ordered validation. Never split randomly.

## Working style

- Read before changing; diagnose read-only before restarting things people use.
- When a choice has a sensible default, take it and say so; ask only when the decision is truly
  the owner's.
- Match the surrounding code: its naming, comment density and idioms.
- Long-running or overnight work: leave a handoff note (what's running, PID, log, next step).
- Finish with concrete next steps rather than "anything else?".
