#!/bin/bash
# usage: nohup final_runs.sh <exe tag: full5> &  round-4 final: metered closure (all on), restart + 4x6 gates, per-switch
# impact runs (one switch off at a time) and default-off run; one or two jobs at a time. Summary in logs/final_<tag>.txt
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
xt=${1:?tag}; out=$E/logs/final_$xt.txt; : > $out
cd $E
cp $E/$xt/ufs-weather-model/tests/fv3_e_$xt.exe exe/ ; cp $E/mq${xt#full}/ufs-weather-model/tests/fv3_e_mq${xt#full}.exe exe/
X=exe/fv3_e_$xt.exe; M=exe/fv3_e_mq${xt#full}.exe
waitj() { while squeue -h -j "$1" 2>/dev/null | grep -q .; do sleep 30; done; }
# nml <dspheat_ke> <samf_cmt_heat> <gwd_ke_heat> <ngw> <K1> <S1> <TFH> <PBK> <D7> <smooth> <cwe>
nml() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = $1\n  samf_cmt_heat = $2\n  gwd_ke_heat = $3\n  ngw_heat_opt = $4\n  thompson_kirchhoff = $5\n  samf_kirchhoff = $6\n  thompson_frame_heat = $7\n  pbl_kirchhoff = $8/; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = $9\n  cpl_ke_smooth = ${10}\n  cpl_water_energy = ${11}/"; }
T=.true.; F=.false.
ALL="$(nml $T $T $T 2 $T $T $T $T $T 2 15)"
j=$(./mkrun.sh m_$xt $M "$ALL" | awk '{print $NF}'); echo "metered all-on $j" >> $out; waitj $j
j=$(./mkrestart.sh rs_$xt $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); waitj $j
j=$(./mkrestart.sh rsL_$xt $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); waitj $j
for v in "noTFH:$(nml $T $T $T 2 $T $T $F $T $T 2 15)" "noPBK:$(nml $T $T $T 2 $T $T $T $F $T 2 15)" \
         "noC8:$(nml $T $T $T 2 $T $T $T $T $T 2 7)" "D7raw:$(nml $T $T $T 2 $T $T $T $T $T 0 15)" \
         "noD7:$(nml $T $T $T 2 $T $T $T $T $F 0 15)" "noS1:$(nml $T $T $T 2 $T $F $T $T $T 2 15)" \
         "off:$(nml $T $F $F 0 $F $F $F $F $F 0 0)"; do
  t=${v%%:*}; s=${v#*:}
  j=$(./mkrun.sh p_${xt}_$t $X "$s" | awk '{print $NF}'); waitj $j
done
cd runs
{
  echo "== gates"
  for p in "rs_${xt}_S rs_${xt}_R restart" "rs_${xt}_S rsL_${xt}_S decomposition" "rs_${xt}_S rsL_${xt}_R decomp+restart" "rs_${xt}_S m_$xt meters-passive"; do
    set -- $p
    for f in atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== closure (metered, all on)"
  $P -I ../tools/frameF_seg.py m_$xt/out
  $P -I ../tools/frameF_table.py m_$xt/out
  echo "== impacts vs all-on straight run (rs_${xt}_S); ctl64 vs ctlc999 is the noise control"
  for t in noTFH noPBK noC8 D7raw noD7 noS1 off; do
    echo "-- $t"; $P -I ../tools/cmp_runs.py rs_${xt}_S p_${xt}_$t 0 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave "
  done
  echo "-- off vs full_off (default-off gate incl. TH8 signal)"; $P -I ../tools/cmp_runs.py full_off p_${xt}_off 0 24 | grep -E " tmp | pressfc | prate_ave "
  echo "-- noise: ctl64 vs ctlc999"; $P -I ../tools/cmp_runs.py ctl64 ctlc999 0 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave "
  echo "-- D7 local heating, step 1: noD7 vs D7raw / noD7 vs all-on (D7S)"
  $P -I ../tools/cmp_runs.py p_${xt}_noD7 p_${xt}_D7raw 0 | grep " tmp "
  $P -I ../tools/cmp_runs.py p_${xt}_noD7 rs_${xt}_S 0 | grep " tmp "
} >> $out 2>&1
echo FINAL DONE >> $out
