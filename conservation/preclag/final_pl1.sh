#!/bin/bash
# usage: nohup final_pl1.sh > logs/final_pl1.nohup 2>&1 & : PL1 gates and closure (all exes -no-fma, inherited from full12).
# ALL = energy final12 switches; ALLC = ALL + sfc_precip_t1_carry. <= 2 own jobs live.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/preclag
Y=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; T=$E/tools; R=$E/runs
out=$P/logs/final_pl1.txt; : > $out; cd $P
mine=""; live() { [ -z "$mine" ] && echo 0 || squeue -h -j $mine 2>/dev/null | wc -l; }
slot() { while [ "$(live)" -ge "${1:-2}" ]; do sleep 60; done; }
for t in pl1 mpl1; do
  until grep -q "BUILD_EXIT" logs/build_$t.*.log 2>/dev/null; do sleep 60; done
  grep -q "BUILD_EXIT rc=0" logs/build_$t.*.log || { echo "ABORT: build $t" >> $out; exit 1; }
  cp $t/ufs-weather-model/tests/fv3_$t.exe exe/ || { echo "ABORT: exe $t" >> $out; exit 1; }
done
ALL="$(cat $E/runs/final12_switches.sed)"
ALLC="${ALL/sfc_precip_enthalpy = .true./sfc_precip_enthalpy = .true.\\n  sfc_precip_t1_carry = .true.}"; [ "$ALLC" != "$ALL" ] || { echo "ABORT: switch edit" >> $out; exit 1; }
echo "$ALLC" > runs/allc_switches.sed
X=exe/fv3_pl1.exe; M=exe/fv3_mpl1.exe
slot; j=$(./mkrun.sh g_off $X "$ALL" | awk '{print $NF}'); mine=$j; echo "g_off (pl1, final12 switches, carry off) job $j" >> $out
slot; j=$(./mkrun.sh m_on $M "$ALLC" | awk '{print $NF}'); mine=$mine,$j; echo "m_on (mpl1, ALLC) job $j" >> $out
slot 1; j=$(./mkrestart.sh rs $X "" "$ALLC" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rs (ALLC) $j" >> $out
slot 1; j=$(./mkrestart.sh rsL $X 4,6 "$ALLC" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); mine=$mine,$j; echo "rsL (ALLC, 4x6) $j" >> $out
slot; j=$(./mkrun.sh m_off $M "$ALL" | awk '{print $NF}'); mine=$mine,$j; echo "m_off (mpl1, final12 switches) job $j" >> $out
slot; j=$(./mkrun.sh gA_off $X | awk '{print $NF}'); mine=$mine,$j; echo "gA_off (pl1, defaults) job $j" >> $out
while [ "$(live)" -gt 0 ]; do sleep 60; done
cd runs
F="atmf000 atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data"
{
  for t in m_on m_off; do echo "=== $t"; grep -o "sfc_precip_t1_carry *= *[.a-z]*" $t/input.nml
    $Y -I $T/frameF_seg.py $t/out; $Y -I ../tools/frameF_table_pl.py $t/out 720 --ep1
    $Y -I $T/eb_table.py $t/out | grep -E "fixer intended|fixer window|Thompson\+MP|ALL physics"; done
  echo "== gates"
  for p in "g_off $R/rs12_S switch-off-vs-full12" "gA_off $R/gA12_off default-off-vs-full12" "rs_S rs_R restart" "rs_S rsL_S decomposition" "rs_S rsL_R decomp+restart" "rs_S m_on meters-passive" "g_off m_off meters-passive-off"; do
    set -- $p
    for f in $F; do
      [[ $3 == meters-passive* ]] && [[ $f == RESTART* ]] && continue
      [[ $3 != *off-vs* ]] && [ $f = atmf000 ] && continue
      echo "$3 $f: $($Y -I $T/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "phy_data variables: rs_S $(ncdump -h rs_S/RESTART/20210323.060000.phy_data.tile1.nc | grep -c 'double\|float') (sfc_precip_t1: $(ncdump -h rs_S/RESTART/20210323.060000.phy_data.tile1.nc | grep -c sfc_precip_t1)), g_off $(ncdump -h g_off/RESTART/20210323.060000.phy_data.tile1.nc | grep -c 'double\|float')"
  echo "== 24 h impact: carry on (rs_S) vs off (full12 all-on rs12_S); noise ctl64 vs ctlc999"
  $Y -I $T/cmp_runs.py $R/rs12_S rs_S 24 | grep -E " tmp | pressfc | prate_ave | lhtfl_ave | shtfl_ave | tmpsfc "
  echo "-- noise"; $Y -I $T/cmp_runs.py $R/ctl64 $R/ctlc999 24 | grep -E " tmp | pressfc | prate_ave | lhtfl_ave | shtfl_ave | tmpsfc "
  echo "== land 0-24 h (imp24.py): carry on vs off / noise ctlc999 vs ctl64"
  $Y -I $T/imp24.py $R/rs12_S rs_S; $Y -I $T/imp24.py $R/ctl64 $R/ctlc999
  echo "== surface fields (sfcimp.py): carry on vs off / noise"
  $Y -I ../tools/sfcimp.py $R/rs12_S rs_S; $Y -I ../tools/sfcimp.py $R/ctl64 $R/ctlc999
} >> $out 2>&1
echo FINAL_PL1 DONE >> $out
