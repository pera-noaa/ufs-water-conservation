#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 1 -c 8 -t 00:20:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer/logs/py_%x.%j.log
# usage: sbatch -J <id> pyjob.sbatch <script.py> [args...]
date -Is
/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I "$@"
echo "=== PY_EXIT rc=$? ==="
