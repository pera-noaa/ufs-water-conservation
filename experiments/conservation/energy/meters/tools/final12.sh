#!/bin/bash
# usage: nohup final12.sh & : full12 = full11 + dyn_te_exact (fv3tally v2), -no-fma. All-on = final11 switches +
# dyn_te_exact = 31 (bug-fix bits); m12_127 = all-on with 127 (+ sponge heat, remap dT). Metered closure and fixer size,
# restart, 3x8 vs 4x6, meters passive, default-off (dyn_te_exact 0) vs bug-fix arm gB11_off, impact vs ctl64 incl. land,
# evcw attribution p12_fwet0 (all-on, noahmp_fwet_opt = 0). <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final12.txt; : > $out; cd $E
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge "${1:-2}" ]; do sleep 60; done; }
until grep -q -E "TREES SUBMITTED|ABORT" logs/mk12.txt; do sleep 60; done
grep -q ABORT logs/mk12.txt && { echo "ABORT: mk12" >> $out; exit 1; }
mine=$(grep "Submitted batch job" logs/mk12.txt | awk '{print $NF}' | paste -sd,)
while [ "$(live)" -gt 0 ]; do sleep 60; done
for t in full12 mq12; do cp $t/ufs-weather-model/tests/fv3_e_$t.exe exe/ || { echo "ABORT: build $t" >> $out; exit 1; }; done
A11="$(cat runs/final11_switches.sed)"
ALL="${A11/dry_tracer_adv = .true./dry_tracer_adv = .true.\\n  dyn_te_exact = 31}"; [ "$ALL" != "$A11" ] || { echo "ABORT: switch edit" >> $out; exit 1; }
A127="${ALL/dyn_te_exact = 31/dyn_te_exact = 127}"; F0="${ALL/noahmp_fwet_opt = 2/noahmp_fwet_opt = 0}"
echo "$ALL" > runs/final12_switches.sed
X=exe/fv3_e_full12.exe; M=exe/fv3_e_mq12.exe
slot; j=$(./mkrun.sh m12 $M "$ALL" | awk '{print $NF}'); mine=$j; echo "m12 job $j" >> $out
slot; j=$(./mkrun.sh m12_127 $M "$A127" | awk '{print $NF}'); mine=$mine,$j; echo "m12_127 job $j" >> $out
slot 1; j=$(./mkrestart.sh rs12 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rs12 $j" >> $out
slot 1; j=$(./mkrestart.sh rsL12 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rsL12 $j" >> $out
slot; j=$(./mkrun.sh gA12_off $X | awk '{print $NF}'); mine=$mine,$j; echo "gA12_off job $j" >> $out
slot; j=$(./mkrun.sh p12_fwet0 $X "$F0" | awk '{print $NF}'); mine=$mine,$j; echo "p12_fwet0 job $j" >> $out
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
{
  for t in m12 m12_127; do echo "=== $t"; grep -o "dyn_te_exact *= *[0-9]*" $t/input.nml
    $P -I ../tools/frameF_seg.py $t/out; $P -I ../tools/frameF_table.py $t/out 720 --ep1
    $P -I ../tools/eb_table.py $t/out | grep -E "fixer intended|fixer window|Thompson\+MP|ALL physics"; done
  echo "== gates"
  for p in "rs12_S rs12_R restart" "rs12_S rsL12_S decomposition" "rs12_S rsL12_R decomp+restart" "rs12_S m12 meters-passive" "gA12_off gB11_off default-off"; do
    set -- $p
    for f in atmf000 atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      [ "$3" != default-off ] && [ $f = atmf000 ] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== 24 h: full12 all-on vs ctl64 (noise in final11.txt)"
  $P -I ../tools/cmp_runs.py ctl64 rs12_S 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc "
  echo "-- dyn_te_exact 31 effect: rs12_S vs full11 all-on rs11_S"; $P -I ../tools/cmp_runs.py rs11_S rs12_S 24 | grep -E " tmp | pressfc | lhtfl_ave "
  echo "== land 0-24 h (imp24.py): all-on vs ctl64 / fwet_opt 0 all-on vs ctl64 / fwet0 vs all-on"
  $P -I ../tools/imp24.py ctl64 rs12_S; $P -I ../tools/imp24.py ctl64 p12_fwet0; $P -I ../tools/imp24.py p12_fwet0 rs12_S
} >> $out 2>&1
echo FINAL12 DONE >> $out
