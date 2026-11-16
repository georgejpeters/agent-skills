#!/usr/bin/env bash
# Wait for a job started by remote-run.sh, then print the log tail and exit with the job's code.
#   remote-wait.sh HOST PID LOG [POLL_SECONDS]
# Always run this with run_in_background: true; you are re-notified when it exits.
# Polls the PID (never `pgrep -f`, which can match its own command line). Tolerates ssh drops:
# the host answering again after a gap is reported, and 20 failed polls in a row gives up with 3.
set -uo pipefail
[[ $# -ge 3 ]] || { echo "usage: remote-wait.sh HOST PID LOG [POLL_SECONDS]" >&2; exit 2; }
HOST=$1 pid=$2 log=$3 poll=${4:-30}
fails=0
while :; do
  if out=$(ssh -o ConnectTimeout=10 -o BatchMode=yes "$HOST" "kill -0 $pid 2>/dev/null && echo alive || echo done" 2>/dev/null); then
    (( fails > 0 )) && echo "$(date -u +%H:%M:%S) host answering again after $fails failed polls"
    fails=0
    [[ $out == done ]] && break
  else
    (( ++fails ))
    (( fails == 3 )) && echo "$(date -u +%H:%M:%S) host not answering (network drop, or the machine is down)"
    (( fails >= 20 )) && { echo "gave up: host unreachable for $((fails * poll))s"; exit 3; }
  fi
  sleep "$poll"
done
ssh -o ConnectTimeout=10 "$HOST" "tail -n 40 $log"
code=$(ssh -o ConnectTimeout=10 "$HOST" "grep -o '^__EXIT=[0-9]*' $log | tail -1 | cut -d= -f2")
if [[ -z $code ]]; then
  echo "job ended without __EXIT: killed (OOM? check: sudo journalctl -k | grep -i oom-kill)"
  exit 4
fi
echo "job exit code: $code"
exit "$code"
