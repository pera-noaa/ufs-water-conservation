#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 4 -t 00:30:00 -J sc_bitcmp -o bitcmp.%j.log
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites_closure; S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites/wb
for t in control_p8_mynn control_iovr4_gfdlmpv3; do
  echo "=== meter vs allfix: $t"; $PY $W/bitcmp.py $S/allfix_$t $W/runs/meter_$t | tail -3
  echo "=== meterfix vs allfix: $t"; $PY $W/bitcmp.py $S/allfix_$t $W/runs/meterfix_$t | tail -2
done
