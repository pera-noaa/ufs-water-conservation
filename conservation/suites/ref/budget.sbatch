#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:00:00
# usage: sbatch -J sc_budget -o budget_<tag>.%j.log budget.sbatch <run names under runs/>
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites_closure
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
for r in "$@"; do
  ( $PY /work2/noaa/co2/ash/ufs-chem-v1/water_budget_by_scheme.py $W/runs/$r > $W/runs/$r/budget_by_scheme.txt 2>&1
    grep -q "WB[MG] " $W/runs/$r/out && $PY $W/meter_report.py $W/runs/$r > $W/runs/$r/meter_report.txt 2>&1 ) &
done
wait
for r in "$@"; do cat $W/runs/$r/budget_by_scheme.txt; [ -e $W/runs/$r/meter_report.txt ] && cat $W/runs/$r/meter_report.txt; done
echo BUDGET_DONE
