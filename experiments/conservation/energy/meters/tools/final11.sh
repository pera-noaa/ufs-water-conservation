#!/bin/bash
# usage: nohup final11.sh & : full11 final (energy r4 + latent + trdyn + ensfc2 r4 + canopy), -no-fma exes. All-on = final9
# switches with LW2 for LW1 + EP1 + AIR1 + noahmp_fwet_opt 2 + thompson_sed_actual + nst_spray_opt 1. Metered closure
# (+ lag meter), restart, 3x8 vs 4x6, meters passive, default-off vs bug-fix arm, impact vs ctl64 incl. land canopy
# evaporation and land LH (imp24.py, canopy's statistic). <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final11.txt; : > $out; cd $E
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge "${1:-2}" ]; do sleep 60; done; }
until grep -q -E "TREES SUBMITTED|ABORT" logs/mk11b.txt; do sleep 60; done
grep -q ABORT logs/mk11b.txt && { echo "ABORT: mk11b" >> $out; exit 1; }
mine=$(grep "Submitted batch job" logs/mk11b.txt | awk '{print $NF}' | paste -sd,)
while squeue -h -n e_full11,e_mq11 2>/dev/null | grep -q .; do sleep 60; done
for t in full11 mq11; do cp $t/ufs-weather-model/tests/fv3_e_$t.exe exe/ || { echo "ABORT: build $t" >> $out; exit 1; }; done
A9="$(cat runs/final9_switches.sed)"
NEW='lw_sfc_return = .true.\n  sfc_precip_enthalpy = .true.\n  noahmp_pore_air = .true.\n  noahmp_fwet_opt = 2\n  thompson_sed_actual = .true.\n  nst_spray_opt = 1'
ALL="${A9/lw_sfc_consistent = .true./$NEW}"; [ "$ALL" != "$A9" ] || { echo "ABORT: switch edit" >> $out; exit 1; }
echo "$ALL" > runs/final11_switches.sed
X=exe/fv3_e_full11.exe; M=exe/fv3_e_mq11.exe
slot; j=$(./mkrun.sh m11 $M "$ALL" | awk '{print $NF}'); mine=$mine,$j; echo "m11 job $j" >> $out
slot 1; j=$(./mkrestart.sh rs11 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rs11 $j" >> $out
slot 1; j=$(./mkrestart.sh rsL11 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rsL11 $j" >> $out
slot 2; j=$(./mkrun.sh gA11_off $X | awk '{print $NF}'); mine=$mine,$j; echo "gA11_off job $j" >> $out
while squeue -h -n e_gB11 2>/dev/null | grep -q .; do sleep 60; done
cp gB11/ufs-weather-model/tests/fv3_e_gB11.exe exe/ || { echo "ABORT: build gB11" >> $out; }
slot 2; j=$(./mkrun.sh gB11_off exe/fv3_e_gB11.exe | awk '{print $NF}'); mine=$mine,$j; echo "gB11_off job $j" >> $out
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
{
  echo "=== m11 (all on)"; grep -c "sfc_precip_enthalpy *= *T\|lw_sfc_return *= *T" m11/out | head -1
  $P -I ../tools/frameF_seg.py m11/out; $P -I ../tools/frameF_table.py m11/out 720 --ep1
  $P -I ../tools/eb_table.py m11/out | grep -E "fixer intended|Thompson\+MP|ALL physics"
  echo "== gates"
  for p in "rs11_S rs11_R restart" "rs11_S rsL11_S decomposition" "rs11_S rsL11_R decomp+restart" "rs11_S m11 meters-passive" "gA11_off gB11_off default-off"; do
    set -- $p
    for f in atmf000 atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      [ "$3" != default-off ] && [ $f = atmf000 ] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== 24 h: full11 all-on vs ctl64; noise ctl64 vs ctlc999"
  $P -I ../tools/cmp_runs.py ctl64 rs11_S 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc | tmp2m "
  echo "-- noise"; $P -I ../tools/cmp_runs.py ctl64 ctlc999 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc | tmp2m "
  echo "== land 0-24 h (imp24.py): all-on vs ctl64 / noise ctlc999 vs ctl64 / full9 all-on vs ctl64"
  $P -I ../tools/imp24.py ctl64 rs11_S; $P -I ../tools/imp24.py ctl64 ctlc999; $P -I ../tools/imp24.py ctl64 rs9_S
} >> $out 2>&1
echo FINAL11 DONE >> $out
