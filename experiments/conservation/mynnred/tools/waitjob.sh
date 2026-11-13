#!/bin/bash
# waitjob.sh <jobid> : poll until the job leaves the queue, then print its state
while true; do
  s=$(broker run --timeout 30 hercules -- "squeue -j $1 -h -o %T 2>/dev/null" 2>/dev/null)
  rc=$?
  if [ $rc -eq 0 ] && [ -z "$s" ]; then break; fi
  sleep 60
done
broker run --timeout 30 hercules -- "sacct -j $1 -X -n -o State,Elapsed | head -1"
