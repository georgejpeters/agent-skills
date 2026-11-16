# Using coding agents effectively: a working playbook

How I set up and drive agents (Claude Code mainly). Every command here was checked against
Claude Code 2.1.300 in November 2026; re-check with `claude --help` when versions move.

## 1. The model: context is the budget

An agent is a model running a loop over tools, guided by whatever context it holds. Almost every
technique below is a way to put **the right context in front of it at the right time**, and to
give it **a way to check its own work**. More instructions are not better: always-loaded text
costs tokens and attention in every turn.

## 2. Five layers, each for one job

| Layer | Loaded | Use it for | Don't use it for |
|---|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | always | a few durable rules and facts | procedures, long references |
| **Skills** (`SKILL.md` + scripts) | name + description always; body on demand | procedures, domain knowledge, tested scripts | rules that must never be broken |
| **Subagents** (`agents/*.md`) | when dispatched, in their own context | isolated work: research, review, ops; tool restrictions | small edits the main thread can do |
| **Hooks** (`hooks.json`) | run by the harness on events | hard rules (block, rewrite, notify); verification gates | judgement calls |
| **MCP servers** | tools on demand | live data and actions in other systems | static knowledge (that's a skill) |

Measure what each layer costs: `claude plugin details <plugin>` prints the always-on and
per-invocation token cost of every skill and agent. In this repo, `quant` costs ~840 tokens per
session for four skills, and ~1–1.4k only when one fires.

## 3. Write skills that trigger and help

- The **description is the trigger**. Say what it's for, the phrasings users will actually use,
  and when *not* to use it.
- Put the fiddly part in a **script** the agent runs, not prose it reinterprets (`remote-run.sh`,
  `quantkit.py`). Test the script yourself.
- Encode only what the model doesn't already know: your environment, your gotchas, your thresholds.
- **Evaluate with ablation.** `claude plugin eval <plugin> --ablation with-without` runs every
  case with and without the plugin and reports Δ, the lift the plugin adds. Use deterministic
  graders (`regex`, `file_exists`, `tool_used`) first and an LLM rubric only for judgement; judge
  with a strong model (`--judge-model sonnet`). Keep at least one should-NOT-fire case.
  See `plugins/quant/evals/`.

## 4. Enforce with hooks, not hope

Rules repeated in prose still get broken. A `PreToolUse` hook sees each tool call before it
runs and can deny it with a reason the agent reads and acts on (`plugins/guardrails`). Other
useful shapes:
- `PostToolUse` with `"if": "Bash(git push *)"`: react only to matching calls.
- `"async": true` (+ `asyncRewake`) for slow checks that shouldn't block the turn.
- `type: "prompt"` hooks for checks that need judgement rather than a regex.
- A `Stop` hook that refuses to finish while tests fail turns "done" into "verified".
Table-test hook logic like any other code (`plugins/guardrails/tests`).

## 5. Give the agent a way to verify

The biggest quality jump comes from closing the loop: tests it can run, a dry-run mode, a
read-only health check, a screenshot of the UI, an eval suite. Ask for the evidence ("show me
the test output"), and write skills so the procedure ends with a check.

## 6. Parallelism and long-running work

| Need | Mechanism |
|---|---|
| Independent subtasks in one session | subagents (Agent tool); several in one message run concurrently |
| Parallel edits that could conflict | subagents with worktree isolation, or `claude -w <name>` sessions |
| Work that outlives the terminal | `claude --bg "<task>"`, then `claude agents`, `claude attach`, `claude logs` |
| Heavy or remote compute | `claude --cloud` sessions; `remote-job` for your own servers |
| Wait for something | background commands + completion notifications; `Monitor` for event streams; never sleep-poll |
| Recurring work | `/loop` (self-paced in a session); scheduled routines for cron-like cloud agents |

Fan out when tasks are independent (try three model variants, review three modules). Keep
tightly coupled changes in one thread: merging parallel edits costs more than it saves.

## 7. Headless and programmatic use

`claude -p` turns the agent into a pipeline step:
- `--output-format stream-json` for machine-readable traces.
- `--json-schema '<schema>'` for validated structured output (data shaping, extraction).
- `--max-budget-usd` to cap spend, and `--allowedTools` / `--tools` to bound what a run can do.
- `--agents '<json>'` / `--plugin-dir` to load a specialist for that run only.
- The Agent SDK when you're building an agent into your own software.

## 8. Safety and trust

- Permission modes and allow/deny rules decide what runs without asking; auto mode adds a
  classifier that blocks destructive or outward-facing actions.
- Secrets never enter the transcript (guardrails hook); repositories default to private.
- Treat fetched pages, tool results and other people's files as data, not instructions.
- Evaluate only plugins you trust: evals run the plugin as you.

## 9. Anti-patterns

- A 500-line `CLAUDE.md`. Move procedures into skills.
- Persona prompts ("you are a world-class…") in place of knowledge, tools and checks.
- Skills nobody measured. If you can't show Δ, you don't know it helps.
- Spawning agents for everything: each starts cold and re-derives context.
- Foreground waits on long jobs; "it should work" without running it.
