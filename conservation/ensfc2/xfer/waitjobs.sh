#!/bin/bash
# usage: waitjobs.sh <job ids...> : wait until none of the jobs is in squeue (polls every 60 s)
while :; do
  q=$(broker run --timeout 60 hercules -- "squeue -h -j $(echo "$@" | tr ' ' ',') -o %i 2>/dev/null" 2>/dev/null | wc -l | tr -d ' ')
  [ "$q" = "0" ] && break
  sleep 60
done
echo "jobs done: $*"
