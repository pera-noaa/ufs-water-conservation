#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 1 -t 00:40:00 -J sc_wb_all -o wb_all.%j.log
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites/wb
for d in allfix_control_p8_mynn orig_control_p8_mynn allfix_rrfs_v1nssl orig_rrfs_v1nssl allfix_hrrr_control orig_hrrr_control allfix_control_iovr4_gfdlmpv3 orig_control_iovr4_gfdlmpv3; do
  WB_END=$( [ -e $W/$d/atmf024.tile1.nc ] && echo 24 || echo 12 ) $PY /work2/noaa/co2/ash/ufs-chem-v1/water_budget_by_scheme.py $W/$d
done
