#!/bin/bash
# usage: runqueue.sh <file of lines "N|remote command"> : submit each when fewer than (3-N) of my e2* jobs are queued
# (N = jobs the line submits); never more than 2 e2* jobs at once. Logs to stdout.
f=${1:?file}
while IFS='|' read -r need cmd; do
  [ -z "$cmd" ] && continue
  while :; do
    n=$(broker run --timeout 60 hercules -- "squeue -h -u apera -o %j | grep -c -E '^e[0-9]([A-Z]|_)' || true" < /dev/null 2>/dev/null | tail -1 | tr -d ' ')
    [ -n "$n" ] && [ $((n + need)) -le 2 ] && break
    sleep 45
  done
  echo "$(date +%H:%M) submit: $cmd"
  broker run --timeout 300 hercules -- "cd /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2 && $cmd" < /dev/null 2>&1 | tail -3
  sleep 5
done < "$f"
echo "QUEUE DONE"
