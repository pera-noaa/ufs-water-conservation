#!/bin/bash
# forecast impact of each change vs pq0, with pq0c (consv_te 0.999) as the threshold-noise control
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/encpl
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
cd $C/runs
for f in atmf024.tile1.nc sfcf024.tile3.nc; do cmp -s $E/runs/fx1/$f pq0/$f && echo "pq0 = fx1 bitwise $f" || echo "pq0 != fx1 $f"; done
for r in ${@:-pq0c pq7 pq1 pq2 pq4 pqK}; do
  echo "=== $r - pq0"
  $PY $C/tools/cmp_runs.py pq0 $r 0 24 | grep -E " tmp | pressfc | prate_ave | lhtfl_ave | spfh "
  $PY $C/tools/cmp_where.py pq0 $r atmf000 tmp | tail -4
  $PY $C/tools/lev_diff.py pq0 $r 24
done
