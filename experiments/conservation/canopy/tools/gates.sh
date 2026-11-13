#!/bin/bash
# usage: nohup gates.sh & : restart (12 h + 12 h) and 4x6 layout gates, all final9 switches + E2 opt2 + TH9 + E1 (b1 exe)
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S="$(cat $C/runs/final9_switches.sed); s/^(\s*lseaspray\s*=[^\n]*)$/\1\n  noahmp_fwet_opt = 2\n  thompson_sed_actual = .true.\n  nst_spray_opt = 1/"
free() { while [ "$(squeue -h -u $USER -o %j | grep -c '^c_\|^cr_')" -gt 0 ]; do sleep 30; done; }
free; $C/tools/mkrestart.sh rsA $C/exe/fv3_c_b1.exe "" "$S"
free; $C/tools/mkrestart.sh rsL $C/exe/fv3_c_b1.exe 4,6 "$S"
free; cd $C/runs
for p in "rsA_S rsA_R restart" "rsA_S rsL_S layout" "rsA_S rsL_R layout+restart"; do set -- $p
  echo "$3 $1 $2: $($P -I ../tools/bitcmp.py $1 $2 24 | tail -1)"; done
grep -c "nst_spray_opt = 1" rsA_S/input.nml rsA_R/input.nml rsL_S/input.nml
echo GATES DONE
