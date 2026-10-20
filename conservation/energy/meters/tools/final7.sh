#!/bin/bash
# usage: nohup final7.sh & : all_full round-4 final (trees full7/mq7: energy r4 + latent + trdyn), all switches on incl.
# dry_tracer_adv: metered closure; tend_opt_pbl 1 and 3; D7 smoothing 8/32 vs off; pbl_kirchhoff off; restart + 4x6 gates
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final7.txt; : > $out
cd $E
cp full7/ufs-weather-model/tests/fv3_e_full7.exe exe/; cp mq7/ufs-weather-model/tests/fv3_e_mq7.exe exe/
X=exe/fv3_e_full7.exe; M=exe/fv3_e_mq7.exe
waitj() { while squeue -h -j "$1" 2>/dev/null | grep -q .; do sleep 30; done; }
# nml <D7> <smooth> <pbl_kirchhoff> <extra gfs_physics_nml lines>
nml() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = .true.\n  samf_cmt_heat = .true.\n  gwd_ke_heat = .true.\n  ngw_heat_opt = 2\n  thompson_kirchhoff = .true.\n  samf_kirchhoff = .true.\n  thompson_frame_heat = .true.\n  pbl_kirchhoff = $3$4/; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = $1\n  cpl_ke_smooth = $2\n  cpl_water_energy = 15\n  dry_tracer_adv = .true./"; }
T=.true.; F=.false.
ALL="$(nml $T 2 $T '')"
echo "$ALL" > $E/runs/final7_switches.sed
for v in "m7:$M:$ALL" "m7_top1:$M:$(nml $T 2 $T '\n  tend_opt_pbl = 1')" "m7_top3:$M:$(nml $T 2 $T '\n  tend_opt_pbl = 3')" \
         "p7_noD7:$X:$(nml $F 0 $T '')" "p7_s8:$X:$(nml $T 8 $T '')" "p7_s32:$X:$(nml $T 32 $T '')" "p7_noPBL:$X:$(nml $T 2 $F '')"; do
  t=${v%%:*}; r=${v#*:}; x=${r%%:*}; s=${r#*:}
  j=$(./mkrun.sh $t $x "$s" | awk '{print $NF}'); echo "$t job $j" >> $out; waitj $j
done
j=$(./mkrestart.sh rs7 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "rs7 $j" >> $out; waitj $j
j=$(./mkrestart.sh rsL7 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "rsL7 $j" >> $out; waitj $j
cd runs
{
  for t in m7 m7_top1 m7_top3; do echo "=== $t"; grep -E "tend_opt_pbl|dry_tracer_adv" $t/input.nml | tr -s " " | tr "\n" " "; echo
    $P -I ../tools/frameF_seg.py $t/out; $P -I ../tools/frameF_table.py $t/out | grep -E "RESIDUAL|fixer|other|r_P|coupling|S_rem|KE:|remainder"; done
  echo "== gates"
  for p in "rs7_S rs7_R restart" "rs7_S rsL7_S decomposition" "rs7_S rsL7_R decomp+restart" "rs7_S m7 meters-passive"; do
    set -- $p
    for f in atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== D7 step-1 heating vs off: s2 (all-on) / s8 / s32"
  for t in rs7_S p7_s8 p7_s32; do $P -I ../tools/cmp_runs.py p7_noD7 $t 0 | grep " tmp "; done
  echo "== 24 h impact vs all-on: noD7, s8, s32, noPBL; noise ctl64 vs ctlc999"
  for t in p7_noD7 p7_s8 p7_s32 p7_noPBL; do echo "-- $t"; $P -I ../tools/cmp_runs.py rs7_S $t 24 | grep -E " tmp | pressfc | lhtfl_ave "; done
} >> $out 2>&1
echo FINAL7 DONE >> $out
