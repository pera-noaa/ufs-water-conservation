#!/bin/bash
# usage: nohup full_matrix.sh &   all_full demo: default-off gate, then (cwe, ngw) in {7,5} x {1,2} metered, gates on 7/1
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $E
for t in all mall; do cp $E/${t}_full/ufs-weather-model/tests/fv3_e_${t}_full.exe $E/exe/; done
K="s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke   = .true./"
sw() { echo "s/^(\s*dspheat\s*=.*)$/\1\n  dspheat_ke = .true.\n  samf_cmt_heat = .true.\n  gwd_ke_heat = .true.\n  ngw_heat_opt = $2\n  thompson_kirchhoff = .true.\n  samf_kirchhoff = .true./; s/^(\s*consv_te\s*=.*)$/\1\n  cpl_ke_heating = .true.\n  cpl_water_energy = $1/"; }
out=$E/logs/full_matrix.txt; : > $out
j=$(./mkrun.sh full_off exe/fv3_e_all_full.exe "$K" | awk '{print $NF}'); while squeue -h -j $j | grep -q .; do sleep 30; done
for f in atmf024 sfcf024; do echo "GATE all_full (only dspheat_ke) vs all_v4k $f: $(cd runs && $P -I ../tools/cmp_allvars.py all_v4k full_off $f 1 | head -1)" >> $out; done
./full_runs.sh full full_c7n1 "$(sw 7 1)" 1
./full_runs.sh full full_c7n2 "$(sw 7 2)" 0
./full_runs.sh full full_c5n1 "$(sw 5 1)" 0
./full_runs.sh full full_c5n2 "$(sw 5 2)" 0
echo MATRIX DONE >> $out
