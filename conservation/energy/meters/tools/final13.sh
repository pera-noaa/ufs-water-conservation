#!/bin/bash
# usage: nohup final13.sh & : full13 = full12 + preclag PL1 + suites 01-08, -no-fma. All-on = final12 switches +
# sfc_precip_t1_carry + gf_closure + mynn_sfc_heat + mynn_mix_sl. Metered closure (preclag lag meter), restart, 3x8 vs 4x6,
# meters passive, default-off vs bug-fix arm gB13, A/B: gB13 vs gB13n05 (does suites 05 change p8) and gB13 vs gB13n08
# (does suites 08 change p8), impact vs ctl64 incl. land. <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final13.txt; : > $out; cd $E
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge "${1:-2}" ]; do sleep 60; done; }
until grep -q -E "TREES SUBMITTED|ABORT" logs/mk13.txt; do sleep 60; done
grep -q ABORT logs/mk13.txt && { echo "ABORT: mk13" >> $out; exit 1; }
mine=$(grep "Submitted batch job" logs/mk13.txt | awk '{print $NF}' | paste -sd,)
ex() { while squeue -h -n e_$1 2>/dev/null | grep -q .; do sleep 60; done; cp $1/ufs-weather-model/tests/fv3_e_$1.exe exe/ || { echo "ABORT: build $1" >> $out; exit 1; }; }
ex full13; ex mq13
A12="$(cat runs/final12_switches.sed)"
ALL="${A12/nst_spray_opt = 1/nst_spray_opt = 1\\n  sfc_precip_t1_carry = .true.\\n  gf_closure = .true.\\n  mynn_sfc_heat = .true.\\n  mynn_mix_sl = .true.}"
[ "$ALL" != "$A12" ] || { echo "ABORT: switch edit" >> $out; exit 1; }; echo "$ALL" > runs/final13_switches.sed
X=exe/fv3_e_full13.exe; M=exe/fv3_e_mq13.exe
slot; j=$(./mkrun.sh m13 $M "$ALL" | awk '{print $NF}'); mine=$mine,$j; echo "m13 job $j" >> $out
slot 1; j=$(./mkrestart.sh rs13 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rs13 $j" >> $out
slot 1; j=$(./mkrestart.sh rsL13 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rsL13 $j" >> $out
slot; j=$(./mkrun.sh gA13_off $X | awk '{print $NF}'); mine=$mine,$j; echo "gA13_off job $j" >> $out
for t in gB13 gB13n05 gB13n08; do ex $t; slot; j=$(./mkrun.sh ${t}_off exe/fv3_e_$t.exe | awk '{print $NF}'); mine=$mine,$j; echo "${t}_off job $j" >> $out; done
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
{
  echo "=== m13 (all on)"; grep -E -o "(sfc_precip_t1_carry|gf_closure|mynn_sfc_heat|mynn_mix_sl|dyn_te_exact) *= *[^ ]*" m13/input.nml | tr "\n" " "; echo
  $P -I ../tools/frameF_seg.py m13/out; $P -I ../tools/frameF_table.py m13/out 720 --ep1
  $P -I ../tools/eb_table.py m13/out | grep -E "fixer intended|PBL \(|Thompson\+MP|ALL physics"
  echo "== gates"
  for p in "rs13_S rs13_R restart" "rs13_S rsL13_S decomposition" "rs13_S rsL13_R decomp+restart" "rs13_S m13 meters-passive" "gA13_off gB13_off default-off" "gB13_off gB13n05_off AB-suites05" "gB13_off gB13n08_off AB-suites08"; do
    set -- $p
    for f in atmf000 atmf006 atmf024 sfcf006 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      [[ "$3" != default-off && "$3" != AB-* ]] && [[ $f == atmf000 || $f == atmf006 || $f == sfcf006 ]] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  for ab in gB13n05_off gB13n08_off; do echo "-- $ab vs gB13_off (f06, f24)"; $P -I ../tools/cmp_runs.py gB13_off $ab 6 | grep -E " tmp | pressfc "; $P -I ../tools/cmp_runs.py gB13_off $ab 24 | grep -E " tmp | pressfc "; done
  echo "== 24 h: full13 all-on vs ctl64 (noise: T 0.149, ps 8.41, LH 3.24)"
  $P -I ../tools/cmp_runs.py ctl64 rs13_S 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc "
  echo "-- full13 vs full12 all-on"; $P -I ../tools/cmp_runs.py rs12_S rs13_S 24 | grep -E " tmp | pressfc | lhtfl_ave "
  echo "== land 0-24 h (imp24.py): all-on vs ctl64 / full13 vs full12"
  $P -I ../tools/imp24.py ctl64 rs13_S; $P -I ../tools/imp24.py rs12_S rs13_S
} >> $out 2>&1
echo FINAL13 DONE >> $out
