---
name: remote-job
description: Run anything non-trivial on a remote machine over ssh — scans, backtests, model training, backfills, data extracts, image pulls, package upgrades, any script over a large dataset. Launches it detached with a log and a memory cap, waits in the background, and reads the result. Use whenever a remote command could take more than ~30 seconds or touch more than a few hundred files. Not for quick reads (git status, tail a log, one ps).
---

# Remote job

Rule: long work on a remote machine never runs in a foreground ssh call, and you keep talking to
the user while it runs. A blocking call freezes the conversation, dies with the connection, and
hides progress. The `guardrails` hook blocks the common shapes; these scripts are the intended
path.

## Launch

```bash
${CLAUDE_PLUGIN_ROOT}/skills/remote-job/scripts/remote-run.sh HOST NAME [-C DIR] -- COMMAND...
# e.g.
${CLAUDE_PLUGIN_ROOT}/skills/remote-job/scripts/remote-run.sh me@server scan -C ~/proj -- .venv/bin/python -m pkg.scan --days 30
```

- Prints `PID=…` and `LOG=~/jobs/<name>-<stamp>.log`. The log ends with `__EXIT=<code>`.
- Survives logout (`setsid nohup`). The command is shipped base64-encoded, so quoting is safe.
- Runs under `ulimit -v` ~6 GB by default so a runaway dies alone instead of taking the machine
  down. Change with `REMOTE_ULIMIT_KB=…`; `0` disables it (needed for tools that reserve large
  virtual memory: JVM, some CUDA/arrow builds) — say so when you do.
- Use the interpreter the project's own scheduled jobs use (check `crontab -l`); don't guess.

## Wait (always in the background)

Run with `run_in_background: true`:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/remote-job/scripts/remote-wait.sh HOST PID LOG
```

Exits with the job's own code. 3 = host unreachable for ~10 min; 4 = the job vanished without
`__EXIT` (likely OOM-killed: check `journalctl -k | grep -i oom-kill`).

In the same turn as the launch, tell the user **what is running, the log path, and an ETA**. Base
the ETA on a previous run's log where there is one (`ls -t ~/jobs/<name>-*.log | head`).

## While it runs

- Peek with a quick `ssh HOST 'tail -5 LOG'`.
- Kill with `ssh HOST 'kill PID'`. If you must match by name, use a bracket pattern
  (`pkill -f 'sca[n]'`) or the pattern matches its own shell.
- Don't stack a second heavy job on a running one without saying so.

## Writing jobs that read a large dataset

The recurring out-of-memory bug: `pd.concat` over every file, then filter. Read each file with
`columns=[…]`, filter it to the slice you need, then concat the parts. Column projection alone
doesn't help when the row count is the problem. Glob by partition (date directory) where you can.
