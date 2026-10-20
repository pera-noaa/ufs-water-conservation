#!/bin/bash
#SBATCH -A co2 -p hercules -N 1 --exclusive -t 00:45:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/patched17r/negr_tools/build_variants.%j.log
# negr variants of patched17r (metered, diff 03 both), each from the pristine sources: f = floor meter, fr = + rain fix, frg = + graupel fix
N=/work2/noaa/co2/ash/ufs-chem-v1/upstream/patched17r
SRC=$N/ufs-weather-model
P=$SRC/UFSATM/ccpp/physics/physics
M=$P/MP/Thompson/module_mp_thompson.F90
D=$P/MP/Thompson/mp_thompson.F90
G=$P/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90
T=$N/negr_tools
PY=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
source /etc/profile >/dev/null 2>&1 || true
module use "$SRC/modulefiles"
module load ufs_hercules.intel
B=$SRC/tests/build_fv3_ups_m17r
[ -f $T/mp_thompson.F90.m17r ] || cp -p $D $T/mp_thompson.F90.m17r
[ -f $T/GFS_physics_post.F90.m17r ] || cp -p $G $T/GFS_physics_post.F90.m17r
restore() { cp $T/module_mp_thompson.F90.m17r_both $M; cp $T/mp_thompson.F90.m17r $D; cp $T/GFS_physics_post.F90.m17r $G; }
for tag in ${VARIANTS:?}; do
  restore
  $PY -I $T/instrument_wb_negr_floor.py $SRC || exit 1
  case $tag in fr) $PY -I $T/fix_thompson_negr_rain_floor.py $SRC || exit 1;; frg) $PY -I $T/fix_thompson_negr_rain_floor.py $SRC --graupel || exit 1;; esac
  cp -p $M $T/module_mp_thompson.F90.m17r_$tag
  cd $B && OMP_NUM_THREADS=1 make -j 40 > $T/make_$tag.log 2>&1; RC=$?
  tail -2 $T/make_$tag.log
  [ $RC = 0 ] || { echo "BUILD FAIL $tag"; break; }
  cp $B/ufs_model $SRC/tests/fv3_ups_m17r_$tag.exe
  cp $SRC/tests/modules.fv3_ups_m17r.lua $SRC/tests/modules.fv3_ups_m17r_$tag.lua
  echo "exe $tag: $(md5sum < $SRC/tests/fv3_ups_m17r_$tag.exe | cut -c1-12)"
done
restore
cd $B && OMP_NUM_THREADS=1 make -j 40 > $T/make_restore.log 2>&1; echo "restore rc=$? $(md5sum < $B/ufs_model | cut -c1-12) vs m17r $(md5sum < $SRC/tests/fv3_ups_m17r.exe | cut -c1-12)"
echo "=== VARIANTS_EXIT ==="
