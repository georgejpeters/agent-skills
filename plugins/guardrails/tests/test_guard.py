"""Table tests for hooks/guard.py: `python3 -I plugins/guardrails/tests/test_guard.py`."""
import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "guard.py"
DENY, ALLOW = "deny", "allow"

BASH = [
    # long jobs on a remote machine
    (DENY, "ssh me@server 'cd ~/proj && .venv/bin/python -m pkg.scan --days 30'", {}),
    (DENY, "ssh -p 2222 me@10.1.2.3 'python3 ~/research/backtest.py'", {}),
    (DENY, "ssh server 'docker compose -f app/docker-compose.yml pull'", {}),
    (DENY, "ssh server 'sudo apt-get upgrade -y'", {}),
    (DENY, "rsync -a data/ me@server:/srv/data/", {}),
    (DENY, "scp big.tar.gz server:/tmp/", {}),
    (DENY, "echo hi", {"timeout": 600000}),
    (DENY, "xcodebuild -scheme App archive -archivePath build/App.xcarchive", {}),
    (DENY, "docker build -t app .", {}),
    (ALLOW, "ssh server 'cd ~/proj && setsid nohup python -m pkg.scan > /tmp/p.log 2>&1 < /dev/null &'", {}),
    (ALLOW, "ssh server 'python3 -m pkg.scan'", {"run_in_background": True}),
    (ALLOW, "ssh server 'python3 -m pkg.registry --list'  # quick: prints a dict", {}),
    (ALLOW, "ssh server 'cd app && git pull --ff-only && docker compose up -d web'", {}),
    (ALLOW, "ssh server 'tail -50 ~/jobs/backtest.log; ls ~/extracted'", {}),
    (ALLOW, "ssh server 'python3 -c \"import numpy; print(numpy.__version__)\"'", {}),
    (ALLOW, "rsync -a src/ /tmp/dst/", {}),
    (ALLOW, "ssh-keygen -t ed25519 -f /tmp/k -N ''", {}),
    (ALLOW, "git status", {"timeout": 60000}),
    # secrets
    (DENY, "cat .env", {}),
    (DENY, "ssh server 'cat ~/app/.env'", {}),
    (DENY, "sudo cat /root/.restic-pass", {}),
    (DENY, "grep API_KEY ~/proj/.env.production", {}),
    (DENY, "cat ~/.netrc", {}),
    (DENY, "cat config/secrets.yaml", {}),
    (DENY, "cat ~/.ssh/id_ed25519", {}),
    (DENY, "sops -d secrets.enc.yaml", {}),
    (DENY, "printenv", {}),
    (DENY, "env | grep TOKEN", {}),
    (DENY, "docker compose --env-file .env config", {}),
    (DENY, "docker inspect web", {}),
    (DENY, "bw get password prod-db", {}),
    (DENY, "op read op://vault/db/password", {}),
    (ALLOW, "cut -d= -f1 .env", {}),
    (ALLOW, "grep -q '^DB_URL=' .env && echo set", {}),
    (ALLOW, "cat .env.example", {}),
    (ALLOW, "cat ~/.ssh/id_ed25519.pub", {}),
    (ALLOW, "sed -i 's/^LOG_LEVEL=.*/LOG_LEVEL=info/' .env", {}),
    (ALLOW, "sops -d secrets.enc.yaml --output /tmp/s.yaml", {}),
    (ALLOW, "docker compose config --services", {}),
    (ALLOW, "docker inspect --format '{{.State.Health.Status}}' web", {}),
    (ALLOW, "cat README.md", {}),
    (ALLOW, "python3 ~/.agent-skills/plugins/guardrails/hooks/env_peek.py .env DATABASE_URL", {}),
]

READ = [
    (DENY, "/home/me/app/.env"),
    (DENY, "/home/me/app/.env.production"),
    (DENY, "/home/me/.ssh/id_rsa"),
    (DENY, "/home/me/app/config/credentials.json"),
    (ALLOW, "/home/me/app/.env.example"),
    (ALLOW, "/home/me/app/README.md"),
    (ALLOW, "/home/me/app/env.py"),
]


def decide(event):
    out = subprocess.run([sys.executable, "-I", str(GUARD)], input=json.dumps(event),
                         capture_output=True, text=True, check=True).stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else ALLOW


def test_env_peek():
    sys.path.insert(0, str(GUARD.parent))
    from env_peek import peek
    cases = {
        "DATABASE_URL=postgres://app:hunter2@db:5432/x": "DATABASE_URL=postgres://app:<masked>@db:5432/x",
        "STRIPE_KEY=sk_live_abc": "STRIPE_KEY=<masked, 11 chars>",
        "export API_TOKEN='t0k3n'": "API_TOKEN=<masked, 5 chars>",
        "WEBHOOK=https://hooks.example.com/services/T0A1B2C3D4E5F6G7H8I9": "WEBHOOK=https://hooks.example.com/services/<masked, 20 chars>",
        "LOG_LEVEL=info": "LOG_LEVEL=info",
        "# comment": "# comment",
    }
    bad = [(k, peek(k), v) for k, v in cases.items() if peek(k) != v]
    for line, got, want in bad:
        print(f"FAIL env_peek {line!r}: got {got!r} want {want!r}")
    return len(cases) - len(bad), len(cases)


def main():
    cases = [(want, {"tool_name": "Bash", "tool_input": {"command": cmd, **extra}}, cmd)
             for want, cmd, extra in BASH]
    cases += [(want, {"tool_name": "Read", "tool_input": {"file_path": p}}, "Read " + p) for want, p in READ]
    failed = 0
    for want, event, label in cases:
        got = decide(event)
        if got != want:
            failed += 1
            print(f"FAIL want={want} got={got}: {label}")
    ok, n = test_env_peek()
    total, failed = len(cases) + n, failed + n - ok
    print(f"{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
