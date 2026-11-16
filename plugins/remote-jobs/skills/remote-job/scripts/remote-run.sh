#!/usr/bin/env bash
# Launch a command on a remote machine fully detached, and print its PID and log path.
#   remote-run.sh HOST NAME [-C DIR] -- COMMAND...
# The command runs under `bash -lc` in DIR (default ~), survives logout, writes stdout+stderr to
# ~/jobs/NAME-<UTC stamp>.log and ends the log with `__EXIT=<code>`. Memory is capped with
# `ulimit -v` (REMOTE_ULIMIT_KB, default 6000000 = ~6 GB; 0 disables) so a runaway dies alone
# instead of OOMing the machine. Wait with remote-wait.sh.
set -euo pipefail
ULIMIT_KB=${REMOTE_ULIMIT_KB:-6000000}

[[ $# -ge 4 ]] || { echo "usage: remote-run.sh HOST NAME [-C DIR] -- COMMAND..." >&2; exit 2; }
HOST=$1 name=$2; shift 2
dir="~"
if [[ $1 == -C ]]; then dir=$2; shift 2; fi
[[ $1 == -- ]] || { echo "remote-run.sh: expected -- before the command" >&2; exit 2; }
shift
[[ $name =~ ^[A-Za-z0-9._-]+$ ]] || { echo "remote-run.sh: NAME must be [A-Za-z0-9._-]" >&2; exit 2; }

stamp=$(date -u +%Y%m%dT%H%M%SZ)
base="jobs/$name-$stamp"
limit=""
[[ $ULIMIT_KB != 0 ]] && limit="ulimit -v $ULIMIT_KB"
script=$(printf '#!/usr/bin/env bash\ncd %s || exit 97\n%s\n(\n%s\n)\necho "__EXIT=$?"\n' "$dir" "$limit" "$*")
payload=$(printf '%s' "$script" | base64 | tr -d '\n')

# Only the job itself is backgrounded, so $! is its PID (setsid execs in place: not a group leader).
ssh -o ConnectTimeout=15 "$HOST" "mkdir -p ~/jobs && echo $payload | base64 -d > ~/$base.sh || exit 1
  setsid nohup bash ~/$base.sh > ~/$base.log 2>&1 < /dev/null & echo \$!" | {
  read -r pid
  echo "started $name on $HOST"
  echo "PID=$pid"
  echo "LOG=~/$base.log"
  echo "wait: remote-wait.sh $HOST $pid ~/$base.log   (run_in_background)"
}
