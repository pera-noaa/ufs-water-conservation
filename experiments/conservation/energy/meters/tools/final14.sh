#!/bin/bash
# usage: nohup final14.sh & : full14 (Ash's decisions: TH8+TH9 unconditional, PL1 folded into EP1, NM10r), -no-fma.
# All-on = final13 switches without thompson_sed_actual and sfc_precip_t1_carry (both gone). Metered all-on (frame F,
# lag, land meter) and all-off (land meter: NM10r phase agreement, Noah-MP water), restart, 3x8 vs 4x6, meters passive,
# default-off vs bug-fix arm gB14, all-on full14 vs full13 (the three edits preserve all-on behaviour), NM10r A/B
# (gB14 vs gB14x, land set vs noise), impact vs ctl64 incl. land. <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final14.txt; : > $out; cd $E
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge "${1:-2}" ]; do sleep 60; done; }
until grep -q -E "TREES SUBMITTED|ABORT" logs/mk14.txt; do sleep 60; done
grep -q ABORT logs/mk14.txt && { echo "ABORT: mk14" >> $out; exit 1; }
mine=$(grep "Submitted batch job" logs/mk14.txt | awk '{print $NF}' | paste -sd,)
ex() { while squeue -h -n e_$1 2>/dev/null | grep -q .; do sleep 60; done; cp $1/ufs-weather-model/tests/fv3_e_$1.exe exe/ || { echo "ABORT: build $1" >> $out; exit 1; }; }
ex full14; ex mq14
A13="$(cat runs/final13_switches.sed)"
ALL="${A13/\\n  thompson_sed_actual = .true./}"; ALL="${ALL/\\n  sfc_precip_t1_carry = .true./}"
[ "$(echo "$ALL" | grep -c -E 'thompson_sed_actual|sfc_precip_t1_carry')" = 0 ] || { echo "ABORT: switch edit" >> $out; exit 1; }
echo "$ALL" > runs/final14_switches.sed
X=exe/fv3_e_full14.exe; M=exe/fv3_e_mq14.exe
slot; j=$(./mkrun.sh m14 $M "$ALL" | awk '{print $NF}'); mine=$mine,$j; echo "m14 job $j" >> $out
slot; j=$(./mkrun.sh m14_off $M | awk '{print $NF}'); mine=$mine,$j; echo "m14_off job $j" >> $out
slot 1; j=$(./mkrestart.sh rs14 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rs14 $j" >> $out
slot 1; j=$(./mkrestart.sh rsL14 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rsL14 $j" >> $out
slot; j=$(./mkrun.sh gA14_off $X | awk '{print $NF}'); mine=$mine,$j; echo "gA14_off job $j" >> $out
for t in gB14 gB14x; do ex $t; slot; j=$(./mkrun.sh ${t}_off exe/fv3_e_$t.exe | awk '{print $NF}'); mine=$mine,$j; echo "${t}_off job $j" >> $out; done
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
{
  for t in m14 m14_off; do echo "=== $t"
    $P -I ../tools/frameF_seg.py $t/out | tail -12; $P -I ../tools/frameF_table.py $t/out 720 --ep1
    $P -I ../tools/eb_table.py $t/out | grep -E "fixer intended|PBL \(|Thompson\+MP|ALL physics" | cut -c1-200
    $P -I ../tools/land14_table.py $t/out; done
  echo "== gates"
  for p in "rs14_S rs14_R restart" "rs14_S rsL14_S decomposition" "rs14_S rsL14_R decomp+restart" "rs14_S m14 meters-passive" "gA14_off gB14_off default-off" "rs13_S rs14_S allon-full13-vs-full14" "gB14_off gB14x_off AB-NM10r"; do
    set -- $p
    for f in atmf000 atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      [[ "$3" != default-off && "$3" != AB-* ]] && [ $f = atmf000 ] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== NM10r A/B (gB14x_off -> gB14_off), land set; noise ctl64 -> ctlc999"
  $P -I ../tools/imp_land14.py gB14x_off gB14_off; $P -I ../tools/imp_land14.py ctl64 ctlc999
  $P -I ../tools/cmp_runs.py gB14x_off gB14_off 24 | grep -E " tmp | pressfc | lhtfl_ave "
  echo "== 24 h: full14 all-on vs ctl64 (noise: T 0.149, ps 8.41, LH 3.24)"
  $P -I ../tools/cmp_runs.py ctl64 rs14_S 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc "
  echo "== land: full14 all-on vs ctl64"; $P -I ../tools/imp_land14.py ctl64 rs14_S
} >> $out 2>&1
echo FINAL14 DONE >> $out
