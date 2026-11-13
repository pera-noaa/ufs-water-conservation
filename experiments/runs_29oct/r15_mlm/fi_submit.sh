#!/bin/bash
# forecast impact (PREREG §2): F = src_f, G = src_g at consv_te 1; noise = G at 0.999 ... 0.990
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm
bash $R/fi_stage.sh F $R/src_f/tests/fv3_atm_dyn32_intel.exe 1.
bash $R/fi_stage.sh G $R/src_g/tests/fv3_mlmg.exe 1.
for m in 1 2 3 4 5 6 7 8 9 10; do c=$(printf '0.%03d' $((1000-m))); bash $R/fi_stage.sh G_$c $R/src_g/tests/fv3_mlmg.exe $c; done
