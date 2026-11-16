# agent-skills

Portable skills, guardrails and working rules for AI coding agents, so every machine I work on
gets the same habits. Mostly for [Claude Code](https://claude.com/claude-code), but the skills are
plain Markdown any assistant can read.

| Plugin | What it gives an agent |
|---|---|
| **guardrails** | A hook that blocks long jobs run in the foreground (remote ssh jobs, bulk copies, builds, raised timeouts) and anything that would print secrets (`.env`, keys, `sops -d`, `docker inspect`…), telling the agent the right way instead. |
| **remote-jobs** | `remote-job` skill: run work on another machine detached, with a log, a memory cap and a background waiter that returns the job's exit code. |
| **quant** | Football and betting quant toolkit. Skills: `football-score-model`, `betting-markets`, `model-validation`, `edge-research`; a `quant` agent; a tested numpy library (`lib/quantkit.py`: Poisson / Dixon-Coles score matrices, team strengths with time decay, de-vig, EV, Kelly, CLV, log loss / RPS / Brier, calibration, bootstrap CIs); and an end-to-end practice pipeline. |

Plus [AGENTS.md](AGENTS.md): the working rules (never block, never expose secrets, evidence over
confidence), imported into every machine's global agent instructions.

## Install on a machine

```bash
git clone https://github.com/georgejpeters/agent-skills ~/.agent-skills && ~/.agent-skills/install.sh
```

This clones the repo, registers it as a Claude Code plugin marketplace, installs the plugins, and
adds one import line for `AGENTS.md` to `~/.claude/CLAUDE.md`. Re-run `install.sh` to update.
Narrow it with `AGENT_SKILLS_PLUGINS="quant" ./install.sh`.

Claude Code only, without cloning:

```bash
claude plugin marketplace add georgejpeters/agent-skills
claude plugin install quant@agent-skills
```

## Use without Claude Code

- **claude.ai**: `python3 scripts/package_skills.py` zips each skill. Upload them under Settings →
  Capabilities → Skills.
- **Any other assistant**: point it at a skill's raw URL, e.g.
  `https://raw.githubusercontent.com/georgejpeters/agent-skills/main/plugins/quant/skills/model-validation/SKILL.md`,
  or paste it in. `lib/quantkit.py` is a single file with only numpy as a dependency.

## Try the quant toolkit

```bash
uv run --no-project --with numpy --with pandas python plugins/quant/examples/practice_pipeline.py
```

A synthetic league with xG and bookmaker odds, walked from data checks through a walk-forward
model, scoring against the market, calibration and betting ROI with confidence intervals, to a
verdict. `--csv` writes the data out to practise on.

## Tests

```bash
python3 -I plugins/guardrails/tests/test_guard.py
uv run --no-project --with numpy python plugins/quant/tests/test_quantkit.py
claude plugin validate . && claude plugin validate plugins/<name>
```

## Private overlays

Machine- or project-specific skills (hostnames, deploy layouts, incident runbooks) belong in a
separate private marketplace installed alongside this one. Nothing here should name a private
host, IP, token or person.

## License

MIT
