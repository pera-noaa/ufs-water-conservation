#!/bin/bash
# usage: nohup frameF_matrix.sh &  : the four all_full variants with the frame-F metered twin (mallq_full), one at a time
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $E; cp mallq_full/ufs-weather-model/tests/fv3_e_mallq_full.exe exe/
sw() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = .true.\n  samf_cmt_heat = .true.\n  gwd_ke_heat = .true.\n  ngw_heat_opt = $2\n  thompson_kirchhoff = .true.\n  samf_kirchhoff = .true./; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = .true.\n  cpl_water_energy = $1/"; }
out=$E/logs/frameF_matrix.txt; : > $out
for v in "7 1" "7 2" "5 1" "5 2"; do
  set -- $v; tag=q_c$1n$2
  j=$(./mkrun.sh $tag exe/fv3_e_mallq_full.exe "$(sw $1 $2)" | awk '{print $NF}')
  while squeue -h -j $j | grep -q .; do sleep 30; done
  echo "=== cpl_water_energy=$1 ngw_heat_opt=$2 (run $tag, job $j); passive vs m_full_c$1n$2: $(cd runs && $P -I ../tools/cmp_allvars.py m_full_c$1n$2 $tag atmf024 1 | head -1)" >> $out
  (cd runs && $P -I ../tools/frameF_table.py $tag/out) >> $out 2>&1
done
echo FRAMEF DONE >> $out
