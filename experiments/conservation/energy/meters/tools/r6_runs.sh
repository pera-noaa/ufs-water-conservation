#!/bin/bash
# usage: nohup r6_runs.sh & : round-4 (tree full6/mq6 incl. PBF + latent): metered all-on closure, tend_opt_pbl 1 and 3,
# D7 smoothing passes 8 and 32 (step-1 heating vs D7 off). Summary in logs/r6.txt
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/r6.txt; : > $out
cd $E
cp full6/ufs-weather-model/tests/fv3_e_full6.exe exe/; cp mq6/ufs-weather-model/tests/fv3_e_mq6.exe exe/
X=exe/fv3_e_full6.exe; M=exe/fv3_e_mq6.exe
waitj() { while squeue -h -j "$1" 2>/dev/null | grep -q .; do sleep 30; done; }
nml() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = .true.\n  samf_cmt_heat = .true.\n  gwd_ke_heat = .true.\n  ngw_heat_opt = 2\n  thompson_kirchhoff = .true.\n  samf_kirchhoff = .true.\n  thompson_frame_heat = .true.\n  pbl_kirchhoff = .true.$3/; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = $1\n  cpl_ke_smooth = $2\n  cpl_water_energy = 15/"; }
for v in "m6:$M:$(nml .true. 2 '')" "m6_top1:$M:$(nml .true. 2 '\n  tend_opt_pbl = 1')" "m6_top3:$M:$(nml .true. 2 '\n  tend_opt_pbl = 3')" \
         "p6_noD7:$X:$(nml .false. 0 '')" "p6_s8:$X:$(nml .true. 8 '')" "p6_s32:$X:$(nml .true. 32 '')"; do
  t=${v%%:*}; r=${v#*:}; x=${r%%:*}; s=${r#*:}
  j=$(./mkrun.sh $t $x "$s" | awk '{print $NF}'); waitj $j; echo "$t job $j" >> $out
done
cd runs
{ for t in m6 m6_top1 m6_top3; do echo "=== $t"; grep -E "tend_opt_pbl" $t/input.nml; $P -I ../tools/frameF_seg.py $t/out; $P -I ../tools/frameF_table.py $t/out | grep -E "RESIDUAL|fixer|other|r_P|coupling|S_rem|KE:|remainder"; done
  echo "=== D7 step-1 heating: noD7 vs s8 / s32"
  $P -I ../tools/cmp_runs.py p6_noD7 p6_s8 0 | grep " tmp "; $P -I ../tools/cmp_runs.py p6_noD7 p6_s32 0 | grep " tmp "
  echo "=== 24h impact s8 vs s32 / noD7 vs s8"; $P -I ../tools/cmp_runs.py p6_s32 p6_s8 24 | grep -E " tmp | pressfc "; $P -I ../tools/cmp_runs.py p6_noD7 p6_s8 24 | grep -E " tmp | pressfc "
} >> $out 2>&1
echo R6 DONE >> $out
