#!/bin/bash
# usage: cmp_all.sh "<A:B> ..." : per pair, cmp_atmf.py on atmf024 and the 24 h RESTART fv_core/fv_tracer/sfc_data/phy_data
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $W/rt
for pr in $PAIRS; do
  a=${pr%%:*}; b=${pr##*:}; echo "=== $a vs $b"
  $P -I $W/bin/cmp_atmf.py $a $b atmf024
  for st in fv_core.res fv_tracer.res sfc_data phy_data; do
    ra=$(ls $a/RESTART/*.$st.tile1.nc 2>/dev/null | sort | tail -1); rb=$(ls $b/RESTART/*.$st.tile1.nc 2>/dev/null | sort | tail -1)
    [ -z "$ra" ] && ra=$a/RESTART/$st.tile1.nc; [ -z "$rb" ] && rb=$b/RESTART/$st.tile1.nc
    mkdir -p $W/x/cmp/$a $W/x/cmp/$b
    for t in 1 2 3 4 5 6; do ln -sf $W/rt/${ra%.tile1.nc}.tile$t.nc $W/x/cmp/$a/r_$st.tile$t.nc; ln -sf $W/rt/${rb%.tile1.nc}.tile$t.nc $W/x/cmp/$b/r_$st.tile$t.nc; done
    $P -I $W/bin/cmp_atmf.py $W/x/cmp/$a $W/x/cmp/$b r_$st
  done
done
