#!/bin/bash
# usage: nohup final9.sh & : all_full final (full9/mq9 = energy r4 + latent + trdyn + ensfc2), everything on:
# metered closure, metered with precip_phase_host off (PH1/D3A check), restart + 4x6 + meters-passive gates
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/final9.txt; : > $out
cd $E
cp full9/ufs-weather-model/tests/fv3_e_full9.exe exe/; cp mq9/ufs-weather-model/tests/fv3_e_mq9.exe exe/
X=exe/fv3_e_full9.exe; M=exe/fv3_e_mq9.exe
waitj() { while squeue -h -j "$1" 2>/dev/null | grep -q .; do sleep 30; done; }
nml() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = .true.\n  samf_cmt_heat = .true.\n  gwd_ke_heat = .true.\n  ngw_heat_opt = 2\n  thompson_kirchhoff = .true.\n  samf_kirchhoff = .true.\n  thompson_frame_heat = .true.\n  pbl_kirchhoff = .true.\n  noahmp_canopy_heat = 1\n  precip_phase_host = $1\n  noahmp_sw_radshare = .true.\n  lw_sfc_consistent = .true.\n  sfc_evap_enthalpy = .true.\n  noahmp_heat_advect = .true.\n  noahmp_kirchhoff = .true./; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = .true.\n  cpl_ke_smooth = 32\n  cpl_water_energy = 15\n  dry_tracer_adv = .true./"; }
ALL="$(nml .true.)"; echo "$ALL" > $E/runs/final9_switches.sed
for v in "m9:$M:$ALL" "m9_noPH:$M:$(nml .false.)"; do
  t=${v%%:*}; r=${v#*:}; x=${r%%:*}; s=${r#*:}
  j=$(./mkrun.sh $t $x "$s" | awk '{print $NF}'); echo "$t job $j" >> $out; waitj $j
done
j=$(./mkrestart.sh rs9 $X "" "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "rs9 $j" >> $out; waitj $j
j=$(./mkrestart.sh rsL9 $X 4,6 "$ALL" | head -1 | sed 's/S=\([0-9]*\) R=\([0-9]*\)/\1,\2/'); echo "rsL9 $j" >> $out; waitj $j
cd runs
{
  for t in m9 m9_noPH; do echo "=== $t"; $P -I ../tools/frameF_seg.py $t/out; $P -I ../tools/frameF_table.py $t/out; done
  echo "== gates"
  for p in "rs9_S rs9_R restart" "rs9_S rsL9_S decomposition" "rs9_S rsL9_R decomp+restart" "rs9_S m9 meters-passive"; do
    set -- $p
    for f in atmf024 sfcf024 RESTART/20210323.060000.fv_core.res RESTART/20210323.060000.fv_tracer.res RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do
      [ "$3" = meters-passive ] && [[ $f == RESTART* ]] && continue
      echo "$3 $f: $($P -I ../tools/cmp_allvars.py $1 $2 $f 1 2>&1 | head -1)"
    done
  done
  echo "== 24 h: all_full final vs ctl64 (total forecast change of the series); noise ctl64 vs ctlc999"
  $P -I ../tools/cmp_runs.py ctl64 rs9_S 24 | grep -E " tmp | ugrd | pressfc | prate_ave | lhtfl_ave | tmpsfc "
} >> $out 2>&1
echo FINAL9 DONE >> $out
