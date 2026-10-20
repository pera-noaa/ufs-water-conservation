#!/bin/bash
# usage: nohup gate10.sh & : default-off gate (gA = full10 every switch off vs gB = fx + bug fixes, both -no-fma) and
# TH8 separability (nth8 = mq10 - TH8, metered, final9 switches, vs m10). Keeps <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/gate10.txt; : > $out; cd $E
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge 2 ]; do sleep 60; done; }
until grep -q "TREES SUBMITTED" logs/mkgate10.txt; do sleep 60; done
mine=$(grep "Submitted batch job" logs/mkgate10.txt | awk '{print $NF}' | paste -sd,)
until [ -s gA/ufs-weather-model/tests/fv3_e_gA.exe ] && [ -s gB/ufs-weather-model/tests/fv3_e_gB.exe ]; do sleep 60; done
while squeue -h -n e_gA,e_gB 2>/dev/null | grep -q .; do sleep 30; done
cp gA/ufs-weather-model/tests/fv3_e_gA.exe gB/ufs-weather-model/tests/fv3_e_gB.exe exe/
slot; a=$(./mkrun.sh gA_off exe/fv3_e_gA.exe | awk '{print $NF}'); mine=$mine,$a; echo "gA_off job $a" >> $out
slot; b=$(./mkrun.sh gB_off exe/fv3_e_gB.exe | awk '{print $NF}'); mine=$mine,$b; echo "gB_off job $b" >> $out
while squeue -h -n e_nth8 2>/dev/null | grep -q .; do sleep 60; done
[ -s nth8/ufs-weather-model/tests/fv3_e_nth8.exe ] && cp nth8/ufs-weather-model/tests/fv3_e_nth8.exe exe/ || { echo "ABORT: nth8 build" >> $out; }
slot; c=$(./mkrun.sh m10_nth8 exe/fv3_e_nth8.exe "$(cat runs/final9_switches.sed)" | awk '{print $NF}'); mine=$mine,$c; echo "m10_nth8 job $c" >> $out
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
{
  echo "== default-off gate: gA_off vs gB_off (-no-fma both)"
  for f in atmf000 atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
    echo "$f: $($P -I ../tools/cmp_allvars.py gA_off gB_off $f 1 2>&1 | head -1)"
  done
  echo "== TH8 separability: m10_nth8 (mq10 - TH8) frame F"
  $P -I ../tools/frameF_seg.py m10_nth8/out; $P -I ../tools/frameF_table.py m10_nth8/out
  $P -I ../tools/eb_table.py m10_nth8/out | grep -i -E "fixer intended|Thompson|dW-Wflux" | head
  echo "== m10_nth8 vs m10 24 h"; $P -I ../tools/cmp_runs.py m10 m10_nth8 24 | grep -E " tmp | pressfc | prate_ave | lhtfl_ave " 
} >> $out 2>&1
echo GATE10 DONE >> $out
