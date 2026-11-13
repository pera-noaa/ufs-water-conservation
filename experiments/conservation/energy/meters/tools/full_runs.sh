#!/bin/bash
# usage: nohup full_runs.sh <exe tag> <run tag> '<input.nml sed -E expression>' [gates=1] &
# After integrate.sh <tag> built exe/fv3_e_{all,mall}_<tag>.exe: metered 24 h closure run, then restart (3x8) and
# restart+decomposition (4x6) gates on the plain exe, one or two jobs at a time; summary in logs/full_<tag>.txt.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
xt=${1:?exe tag}; tag=${2:?run tag}; nml=${3:-}; gates=${4:-1}
out=$E/logs/full_$tag.txt; : > $out
waitjobs() { while squeue -h -j "$1" 2>/dev/null | grep -q .; do sleep 30; done; }
cd $E
for t in all mall; do [ -e $E/exe/fv3_e_${t}_$xt.exe ] || cp $E/${t}_$xt/ufs-weather-model/tests/fv3_e_${t}_$xt.exe $E/exe/ || { echo "no exe ${t}_$xt" >> $out; exit 1; }; done
j=$(./mkrun.sh m_$tag exe/fv3_e_mall_$xt.exe "$nml" | awk '{print $NF}'); echo "metered run $j" >> $out; waitjobs $j
if [ "$gates" = 1 ]; then
j=$(./mkrestart.sh rs_$tag exe/fv3_e_all_$xt.exe "" "$nml" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "restart 3x8 $j" >> $out; waitjobs $j
j=$(./mkrestart.sh rsL_$tag exe/fv3_e_all_$xt.exe 4,6 "$nml" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "restart 4x6 $j" >> $out; waitjobs $j
fi
cd $E/runs
{
  echo "== switches: $nml"
  grep -E "^\s*(dspheat_ke|cpl_ke_heating|cpl_water_energy|samf_cmt_heat|gwd_ke_heat|ngw_heat_opt|thompson_kirchhoff|samf_kirchhoff)\s*=" m_$tag/input.nml | tr -s " " | tr "\n" " "; echo
  if [ "$gates" = 1 ]; then echo "== gates (0 of N variables differ = bit-identical)"
  for p in "rs_${tag}_S rs_${tag}_R restart" "rs_${tag}_S rsL_${tag}_S decomposition" "rs_${tag}_S rsL_${tag}_R decomp+restart" "rs_${tag}_S m_$tag meters-passive"; do
    set -- $p
    for f in atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done; fi
  echo "== per-segment and global budget (metered)"
  $P -I ../tools/eb_table.py m_$tag/out | grep -E "r=dE|global budget" -A0
  $P -I ../tools/eb_table.py m_$tag/out | sed -n "/global budget/,\$p"
} >> $out 2>&1
echo DONE >> $out
