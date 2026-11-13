#!/bin/bash
# round 1 cases: 1 h (na_init 0, identical state at step 1) and 24 h (na_init 1, as fv3tally)
set -euo pipefail
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/dycred; EXE=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/fv3tally/exe/fv3_t_fx.exe
M=$D/tools/mkcase.sh
X() { echo "s/^(\s*consv_te\s*=.*)$/\1\n  dyn_te_exact = $1/"; }
DC() { echo "s/^(\s*d_con\s*=\s*).*/\1$1/"; }
$M h_d1  $EXE 1 0
$M h_d0  $EXE 1 0 "$(DC 0.)"
$M h_d05 $EXE 1 0 "$(DC 0.5)"
$M h_x1  $EXE 1 0 "$(X 1)"
$M h_x16 $EXE 1 0 "$(X 16)"
$M h_x17 $EXE 1 0 "$(X 17)"
$M h_nod $EXE 1 0 "$(DC 0.)" "s/^(\s*d4_bg\s*=\s*).*/\10./" "s/^(\s*dddmp\s*=\s*).*/\10./" "s/^(\s*vtdm4\s*=\s*).*/\10./"
$M h_r0  $EXE 1 0 "s/^(\s*tau\s*=\s*).*/\10./"
$M h_x8  $EXE 1 0 "$(X 8)"
$M d_d1  $EXE 24 1
$M d_x1  $EXE 24 1 "$(X 1)"
$M d_d0  $EXE 24 1 "$(DC 0.)"
