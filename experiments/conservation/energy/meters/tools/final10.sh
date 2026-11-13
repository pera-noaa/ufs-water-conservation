#!/bin/bash
# usage: nohup final10.sh & : trdyn v5 -> 04_INLQ + v6 swap check (inline_q off): full10 all-on vs full9 (rs9_S) and
# metered mq10 vs m9, same switches (runs/final9_switches.sed)
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final10.txt; : > $out
cd $E
while squeue -h -n e_mq10,e_full10 2>/dev/null | grep -q .; do sleep 60; done
cp full10/ufs-weather-model/tests/fv3_e_full10.exe exe/ || exit 1; cp mq10/ufs-weather-model/tests/fv3_e_mq10.exe exe/ || exit 1
ALL="$(cat runs/final9_switches.sed)"
a=$(./mkrun.sh p10 exe/fv3_e_full10.exe "$ALL" | awk '{print $NF}'); b=$(./mkrun.sh m10 exe/fv3_e_mq10.exe "$ALL" | awk '{print $NF}')
echo "p10 job $a m10 job $b" >> $out
while squeue -h -j $a,$b 2>/dev/null | grep -q .; do sleep 30; done
cd runs
{
  for p in "rs9_S p10" "m9 m10" "p10 m10"; do set -- $p
    for f in atmf024 sfcf024; do echo "$1 vs $2 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"; done
  done
  $P -I ../tools/frameF_seg.py m10/out; $P -I ../tools/frameF_table.py m10/out
} >> $out 2>&1
echo FINAL10 DONE >> $out
