"""Print a .env-style file with secrets masked, so an agent can debug config without leaking it.

    python3 env_peek.py .env [KEY ...]

Masks: values of keys that look secret (PASS, SECRET, TOKEN, KEY, PRIVATE, CRED, AUTH, SALT,
COOKIE, SESSION), the password part of URLs (scheme://user:PASS@host), and any long
token-looking run of characters in other values. Shows everything else (hosts, ports, flags).
"""
import re
import sys

SECRET_KEY = re.compile(r"PASS|SECRET|TOKEN|KEY|PRIVATE|CRED|AUTH|SALT|COOKIE|SESSION", re.I)
URL_PASSWORD = re.compile(r"(\w+://[^:/@\s]+:)([^@\s]+)(@)")
TOKENISH = re.compile(r"(?=[A-Za-z0-9_\-+=]*\d)(?=[A-Za-z0-9_\-+=]*[A-Za-z])[A-Za-z0-9_\-+=]{20,}")


def mask(value):
    return f"<masked, {len(value)} chars>" if value else "<empty>"


def peek(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return line.rstrip("\n")
    key, _, value = stripped.partition("=")
    key = key.removeprefix("export ").strip()
    value = value.strip().strip("'\"")
    if SECRET_KEY.search(key):
        return f"{key}={mask(value)}"
    value = URL_PASSWORD.sub(lambda m: m.group(1) + "<masked>" + m.group(3), value)
    value = TOKENISH.sub(lambda m: mask(m.group(0)), value)
    return f"{key}={value}"


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: env_peek.py FILE [KEY ...]")
    wanted = set(sys.argv[2:])
    with open(sys.argv[1]) as f:
        for line in f:
            key = line.split("=", 1)[0].removeprefix("export ").strip()
            if not wanted or key in wanted:
                print(peek(line))


if __name__ == "__main__":
    main()
