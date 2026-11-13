#!/bin/bash
# chk16b_chain.sh : rebuild ensfc2's chain on a copy of energy/fx ccpp (04-06, 08-11, NM12, 13-15), then dry-run 16 and 16b;
# apply 16b and compare the 16-touched files with full12 (diff counts only)
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; P=$U/cons/preclag; S=$U/cons/ensfc2/patches
W=$P/chk16; rm -rf "${W:?}"; mkdir -p $W/fx/ufs-weather-model/UFSATM
rsync -a $E/fx/ufs-weather-model/UFSATM/ccpp $W/fx/ufs-weather-model/UFSATM/
cd $W
for d in $S/04_sfc_SI1.diff $S/05_sfc_SI2.diff $S/06_sfc_NP1.diff $S/08_sfc_QR1.diff $S/09_sfc_CMC.diff $S/10_sfc_FL1.diff $S/11_sfc_options.diff $E/accepted/07_NM12_noahmp_combine_melt_out.diff $S/13_sfc_SL2.diff $S/14_sfc_CS1.diff $S/15_sfc_CB1.diff; do
  pl=1; head -3 $d | grep -q "^--- fx/" || pl=0
  r=$(patch -p$pl -F0 < $d 2>&1 | grep -c -i "FAILED\|can't find"); echo "$(basename $d) p$pl failed-hunks $r"
done
echo "16  dry: $(patch -p1 -F0 --dry-run < $S/16_sfc_options_r4.diff | grep -c FAILED)"
echo "16b dry: $(patch -p1 -F0 --dry-run < $P/patches/16b_sfc_options_r4_meta_fixed.diff | grep -c FAILED)"
patch -p1 -F0 < $P/patches/16b_sfc_options_r4_meta_fixed.diff | grep -c FAILED
for f in $(grep '^+++ ' $P/patches/16b_sfc_options_r4_meta_fixed.diff | awk '{print $2}'); do
  g=${f#fx/}; echo "$(basename $f): lines differing from full12 $(diff $W/$f $E/full12/$g | grep -c '^[<>]')"
done
