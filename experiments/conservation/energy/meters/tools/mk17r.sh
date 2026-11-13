#!/bin/bash
# usage: mk17r.sh : standalone water diff 17r (NM10 + NM10r) against develop @112b1d46 (ccpp-physics 242a2fc) + 01-16.
# w16 = pristine physics + 01..16 (09b is the noahmp-emc companion, 19 is FV3: not in this repo); w17r = w16 + 17 + ensfc2
# 12_sfc_NM10r (paths fx/ufs-weather-model/UFSATM/ccpp/physics/... -> -p5). 17r = w16 -> w17r. Checks: 17r applies -F0 on w16;
# 18 applies -F0 after 17r; w17r == w16 + 17 + NM10r.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/ufs-weather-model/UFSATM/ccpp/physics
W=$E/water17r; Q=$W/patches; N10=$E/accepted/42_ensfc2_12_sfc_NM10r.diff
for d in w16 w17r chk; do x=$W/$d; rm -rf "${x:?}"; done
rsync -a --exclude=.git $S/ $W/w16/
cd $W/w16; for f in $(ls $Q/0*.diff $Q/1[0-6]_*.diff); do patch -p1 -F0 -s < $f || { echo "ABORT: $(basename $f) on w16"; exit 1; }; done; echo "w16 = 242a2fc + 01..16"
rsync -a $W/w16/ $W/w17r/; cd $W/w17r
patch -p1 -F0 -s < $Q/17_NM10_noahmp_precip_phase.diff || { echo "ABORT: 17"; exit 1; }
patch -p5 -F0 < $N10 || { echo "ABORT: NM10r on w16+17 (-F0)"; exit 1; }
find $W/w17r -name "*.orig" -delete
cd $W; diff -ruN w16 w17r | sed -e "s|^--- w16/|--- a/|" -e "s|^+++ w17r/|+++ b/|" -e "/^diff -ruN/d" > $W/17r_NM10r_noahmp_precip_phase.diff
echo "17r: $(lsdiff $W/17r_NM10r_noahmp_precip_phase.diff | tr '\n' ' ') $(grep -c '^[-+][^-+]' $W/17r_NM10r_noahmp_precip_phase.diff) changed lines"
rsync -a $W/w16/ $W/chk/; cd $W/chk
patch -p1 -F0 -s < $W/17r_NM10r_noahmp_precip_phase.diff && echo "17r applies -F0 on w16" || echo "FAIL 17r on w16"
patch -p1 -F0 -s < $Q/18_NM11_noahmp_ground_vapour_latent_heat.diff && echo "18 applies -F0 after 17r" || echo "FAIL 18 after 17r"
d=$W/chk; rm -rf "${d:?}"
