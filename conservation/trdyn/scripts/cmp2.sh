#!/bin/bash
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; cd $W/rt
for pr in c0:o0 o0:a1 e2:e2L e2:e2R n0:i1; do a=${pr%%:*}; b=${pr##*:}; echo "=== $a vs $b"; $P -I $W/bin/cmp_atmf.py $a $b atmf024; done
echo "=== e2 vs e2R 018"; $P -I $W/bin/cmp_atmf.py e2 e2R atmf018
echo "=== e2L vs e2R RESTART 24h"
for st in fv_core.res fv_tracer.res sfc_data phy_data; do mkdir -p $W/x/cmp2/e2L $W/x/cmp2/e2R
  for t in 1 2 3 4 5 6; do for r in e2L e2R; do ln -sf $W/rt/$r/RESTART/20210323.060000.$st.tile$t.nc $W/x/cmp2/$r/r_$st.tile$t.nc; done; done
  $P -I $W/bin/cmp_atmf.py $W/x/cmp2/e2L $W/x/cmp2/e2R r_$st; done
echo "=== tracer impact o0 -> a1 (class c), n0 -> e2 (c+d)"
$P -I $W/bin/cmp_dyn.py o0 a1 024; $P -I $W/bin/cmp_dyn.py n0 e2 024; $P -I $W/bin/cmp_dyn.py o0 o0 000
