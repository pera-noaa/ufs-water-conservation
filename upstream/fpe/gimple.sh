#!/bin/bash
set -u
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/fms_codegen
eval "$(grep -E '^(FC|M|S|DEFS|INC|BASE)=' $W/codegen.sh)"
mkdir -p $W/b_dump && cd $W/b_dump
$FC $DEFS $INC $BASE -O3 -funroll-all-loops -finline-functions -march=icelake-client -mtune=icelake-client -J. \
  -fdump-tree-ifcvt -fdump-tree-vect-details -fdump-tree-optimized -fdump-rtl-expand -c $S/diag_manager/diag_manager.F90 -o dm.o 2>&1 | tail -3
ls
echo "== internal fns in optimized"
grep -ohE '\.(COND_[A-Z_]+|MASK_LOAD|MASK_STORE|FMA|VCOND[A-Z_]*)' *.optimized | sort | uniq -c
echo "== ifcvt: COND fns"
grep -ohE '\.(COND_[A-Z_]+|MASK_LOAD|MASK_STORE|FMA)' *.ifcvt | sort | uniq -c
echo "== vect notes for source lines 2529-2546"
grep -E 'diag_manager.F90:25(29|3[0-9]|4[0-6]):[0-9]+: (optimized|note:   (vectorizing stmts|loop vectorized))' *.vect | head -10
