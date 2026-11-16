"""PreToolUse guard for Claude Code's Bash and Read tools.

Two rules, enforced instead of remembered:

1. Long-running work never runs in the foreground: remote jobs over ssh, bulk copies, builds,
   installs, and any command given a raised timeout. The agent should background it, log it,
   and keep talking.
2. Secrets never get printed into the transcript: .env files, key files, decrypted sops output,
   whole-environment dumps, `docker compose config`, `docker inspect`, password-manager items.

A denial explains the right pattern, so the agent can retry correctly. A long-job false
positive can be overridden with a `# quick: <reason>` comment; secrets have no override.
"""
import json
import os
import re
import sys

SSH = re.compile(r"\bssh\b(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+[\w.@-]+")
REMOTE_COPY = re.compile(r"\b(?:rsync|scp)\b[^\n|;&]*\s[\w.-]+@?[\w.-]*:")
DETACHED = re.compile(r"\b(?:nohup|setsid|systemd-run|tmux\s+new|screen\s+-d|remote-run\.sh)\b")
LONG_REMOTE = re.compile(
    r"\bpython[0-9.]*\s+(?:-u\s+)?(?:-m\s|\S+\.py\b)"
    r"|\b(?:backtest|backfill|walkforward|train|memtester|stress-ng|make|cargo\s+build|go\s+build)\b(?!\.\w)"
    r"|\brestic\s+(?:backup|check|prune|restore)\b"
    r"|\bapt(?:-get)?\s+(?:upgrade|full-upgrade|install|dist-upgrade)\b"
    r"|\bdocker(?:\s+compose)?\b[^|;&\n]*\s(?:build|pull)\b"
    r"|\b(?:pip|uv)\s+(?:install|sync)\b|\bnpm\s+(?:install|ci)\b"
)
LOCAL_LONG = re.compile(
    r"\bxcodebuild\b[^\n]*\b(?:archive|build|test|-exportArchive)\b|\bxcrun\s+(?:altool|notarytool)\b"
    r"|\bdocker\s+build\b"
)
QUICK = re.compile(r"#\s*quick:")
FOREGROUND_TIMEOUT_MS = 120_000

SECRET_PATH = re.compile(
    r"(?:^|[\s/'\"=])\.env(?:\.(?!example|sample|template)[\w.-]+)?(?=$|[\s'\";|&)])"
    r"|\.restic[\w.-]*pass\b|\.netrc\b|\.pgpass\b|\w+\.cred\b|\bcredentials\.json\b"
    r"|\b\w*secrets?\.(?:ya?ml|json|env|toml)\b"
    r"|\b\w*(?:key|private)\w*\.pem\b|\bid_(?:rsa|ed25519|ecdsa)(?!\.pub)\b"
)
READER = re.compile(r"\b(?:cat|less|more|head|tail|bat|strings|xxd|od|nl|awk|grep|rg|diff|sed|base64|tee)\b")
KEYS_ONLY = re.compile(
    r"cut\s+-d\s*['\"]?=['\"]?\s+-f\s*1|sed\s+['\"]?s/=\.\*//|grep\s+-[a-zA-Z]*[cqlL]"
    r"|grep\s+-o\s+['\"]?\^\[|\bsed\s+-i\b"
)
OTHER_LEAKS = [
    (re.compile(r"\bsops\b[^\n]*\s(?:-d|--decrypt)\b(?![^\n]*(?:>|--output|exec-env|exec-file))"),
     "sops decrypt to stdout prints the plaintext. Decrypt to a file (`--output`) or use `sops exec-env`."),
    (re.compile(r"(?:^|[;&|]\s*|\bexec\s+\S+\s+|ssh\s+\S+\s+['\"]?)(?:printenv|env)\s*(?:$|[|;&'\"])"),
     "dumping the whole environment prints tokens. Print one non-secret variable, or `env | cut -d= -f1` for names."),
    (re.compile(r"\b(?:bw|op)\s+(?:get|read)\s+(?:password|item|notes|totp|op://)"),
     "password-manager items stay out of the transcript. Pipe them straight into the consumer."),
    (re.compile(r"\bdocker(?:\s+compose)?\b[^|;&\n]*\sconfig\b(?![^\n]*(?:--services|--volumes|--images|-q\b|--quiet))"),
     "`docker compose config` prints the resolved .env secrets. Use `config --services`, or `config -q` to validate."),
    (re.compile(r"\bdocker\s+(?:container\s+)?inspect\b(?![^\n]*(?:--format|-f\s))"),
     "`docker inspect` prints the container env including secrets. Use `--format` to pick the fields you need."),
]


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "guardrails: " + reason,
    }}))
    sys.exit(0)


def check_read(tool_input):
    path = tool_input.get("file_path", "")
    if SECRET_PATH.search(" " + os.path.basename(path)):
        deny(f"{path} holds secrets and must not be read into the transcript. "
             "List key names with `cut -d= -f1 <file>`; test one value with `grep -q '^KEY=' <file>`.")


def check_secrets(cmd):
    if SECRET_PATH.search(cmd) and READER.search(cmd) and not KEYS_ONLY.search(cmd):
        deny("this would print a secrets file (.env, key, credentials) into the transcript. "
             "List key names with `cut -d= -f1 <file>`, test a value with `grep -q '^KEY=' <file>`, "
             "or edit in place with `sed -i`.")
    for pattern, why in OTHER_LEAKS:
        if pattern.search(cmd):
            deny(why)


def check_long(cmd, tool_input):
    if tool_input.get("run_in_background") or QUICK.search(cmd):
        return
    timeout = tool_input.get("timeout") or 0
    if timeout > FOREGROUND_TIMEOUT_MS:
        deny(f"a {timeout // 1000}s timeout means this belongs in the background. Re-run with "
             "run_in_background: true writing to a log, and tell the user what is running, where the "
             "log is and the ETA.")
    if REMOTE_COPY.search(cmd):
        deny("bulk copies to another machine run in the background (run_in_background: true). Use "
             "`rsync -a --partial --timeout=120` in a retry loop so a dropped link resumes.")
    if SSH.search(cmd) and LONG_REMOTE.search(cmd) and not DETACHED.search(cmd):
        deny("this looks like a long job on a remote machine, run in the foreground. Launch it "
             "detached (the remote-job skill's remote-run.sh, or `setsid nohup ... > log 2>&1 < "
             "/dev/null &`), then wait with run_in_background. If it really takes seconds, append "
             "`# quick: <reason>`.")
    if LOCAL_LONG.search(cmd):
        deny("builds, archives and uploads run in the background (run_in_background: true, log to a file).")


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    tool, tool_input = event.get("tool_name"), event.get("tool_input") or {}
    if tool == "Read":
        check_read(tool_input)
    elif tool == "Bash":
        cmd = tool_input.get("command", "")
        check_secrets(cmd)
        check_long(cmd, tool_input)


if __name__ == "__main__":
    main()
