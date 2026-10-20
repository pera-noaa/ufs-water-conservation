#!/bin/bash
# usage: mkrun.sh <name> <exe> [VAR=VAL ...] ; make run dir via make_rundir.sh, export VARs in job_card, submit
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trsamf
n=${1:?}; e=${2:?}; shift 2
bash $W/bin/make_rundir.sh "$n" "$e" 40 > $W/logs/mkrun_$n.log 2>&1 || { tail -5 $W/logs/mkrun_$n.log; exit 1; }
cd $W/rt/$n
for kv in "$@"; do sed -i "s/^export OMP_NUM_THREADS=1$/export OMP_NUM_THREADS=1\nexport $kv/" job_card; done
grep -E "^export (OMP_NUM_THREADS|TRSAMF)" job_card | tr '\n' ' '
sbatch job_card
