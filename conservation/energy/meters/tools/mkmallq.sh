#!/bin/bash
# usage: nohup mkmallq.sh <tag> &  : $E/mallq_<tag> = $E/mall_<tag> + encpl frame-F coupling meter (meter_r2), then build
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
tag=${1:?tag}; S=$E/mall_$tag; D=$E/mallq_$tag
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
cd $D/ufs-weather-model
patch -p1 -F0 -s < $E/pending/meter_r2_encpl.diff > $E/logs/mallq_$tag.patch.log 2>&1 || true
# the one hunk that clashes only with D7's neighbouring use line
A=UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90
grep -q "ebq, ebq_prc" $A || sed -i "s/^use fv_mapz_mod,       only: eb_state, eb_print, ebx$/use fv_mapz_mod,       only: eb_state, eb_print, ebx, ebq, ebq_prc/" $A
rm -f $A.rej $A.orig
find . -name "*.rej" | tee -a $E/logs/mallq_$tag.patch.log
grep -c "ebq, ebq_prc" $A
cd $E && sbatch -J e_mallq_$tag --export=NONE,SRC=$D/ufs-weather-model,CLEAN=YES build64.sbatch
