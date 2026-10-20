#!/bin/bash
# mkdiffs.sh : 01_PL1 fix diff (full12 -> pl1) and meter diff (mq12 + PL1 -> mpl1, meter files only); -p1 from ufs-weather-model.
# Checks: fix diff applies -F0 on full12 and on mq12 copies (dry run); fix files of mpl1 == mq12 + fix diff.
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; P=$U/cons/preclag
C=UFSATM/ccpp; NE=$C/physics/physics/Interstitials/UFS_SCM_NEPTUNE; NM=$C/physics/physics/SFC_Models/Land/Noahmp; SI=$C/physics/physics/SFC_Models/SeaIce/CICE
FIX="$C/data/GFS_typedefs.F90 $C/data/GFS_typedefs.meta $C/driver/GFS_restart.F90 $NE/GFS_MP_generic_post.F90 $NE/GFS_MP_generic_post.meta $NM/noahmpdrv.F90 $NM/noahmpdrv.meta $NM/module_sf_noahmplsm.F90 $NM/module_sf_noahmp_glacier.F90 $SI/sfc_sice.f $SI/sfc_sice.meta"
MET="$NE/energy_meter_common.F90 $NE/em_p01.F90 $NE/em_p01.meta $NE/em_p12.F90"
F=$P/patches/01_PL1_sfc_precip_t1_carry.diff; M=$P/patches/meter_PL1_lag_v2.diff
: > $F; for f in $FIX; do diff -u --label a/$f --label b/$f $E/full12/ufs-weather-model/$f $P/pl1/ufs-weather-model/$f >> $F; done
: > $M; for f in $MET; do diff -u --label a/$f --label b/$f $E/mq12/ufs-weather-model/$f $P/mpl1/ufs-weather-model/$f >> $M; done
echo "fix: $(grep -c '^+[^+]' $F) added, $(grep -c '^-[^-]' $F) removed, md5 $(md5sum < $F | cut -c1-12)"
echo "meter: $(grep -c '^+[^+]' $M) added, $(grep -c '^-[^-]' $M) removed, md5 $(md5sum < $M | cut -c1-12)"
for t in full12 mq12; do echo "fix dry-run on $t: $(cd $E/$t/ufs-weather-model && patch -p1 -F0 --dry-run < $F | grep -c -i 'FAIL\|offset\|fuzz') fail/offset lines"; done
W=$P/xfer/chkfix; rm -rf "${W:?}"; mkdir -p $W
for f in $FIX; do mkdir -p $W/$(dirname $f); cp $E/mq12/ufs-weather-model/$f $W/$f; done
(cd $W && patch -s -p1 -F0 < $F)
n=0; for f in $FIX; do cmp -s $W/$f $P/mpl1/ufs-weather-model/$f || { echo "DIFFERS $f"; n=1; }; done; echo "mq12 + fix == mpl1 fix files: $([ $n = 0 ] && echo yes || echo NO)"
rm -rf "${W:?}"
