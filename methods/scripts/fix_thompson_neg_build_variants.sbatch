#!/bin/bash
#SBATCH -A co2 -p hercules -N 1 --exclusive -t 00:45:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/patched17n/neg_tools/build_variants.%j.log
# fix_thompson_neg_build_variants.sbatch: builds fix variants of patched17n (metered) one after another: each from the pristine metered source + fix_thompson_neg_csed_rcs.py.
N=/work2/noaa/co2/ash/ufs-chem-v1/upstream/patched17n
SRC=$N/ufs-weather-model
M=$SRC/UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90
PY=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
source /etc/profile >/dev/null 2>&1 || true
module use "$SRC/modulefiles"
module load ufs_hercules.intel
B=$SRC/tests/build_fv3_ups_m17n
[ -f $N/neg_tools/module_mp_thompson.F90.m17n2 ] || cp -p $M $N/neg_tools/module_mp_thompson.F90.m17n2
for v in ${VARIANTS:?}; do
  tag=${v%%:*}; args=${v#*:}; args=${args//+/ }
  cp $N/neg_tools/module_mp_thompson.F90.m17n2 $M
  $PY -I $N/neg_tools/fix_thompson_neg_csed_rcs.py $SRC $args || exit 1
  cd $B && OMP_NUM_THREADS=1 make -j 40 > $N/neg_tools/make_$tag.log 2>&1; RC=$?
  tail -2 $N/neg_tools/make_$tag.log
  [ $RC = 0 ] || { echo "BUILD FAIL $tag"; break; }
  cp $B/ufs_model $SRC/tests/fv3_ups_m17n_$tag.exe
  cp $SRC/tests/modules.fv3_ups_m17n.lua $SRC/tests/modules.fv3_ups_m17n_$tag.lua
  echo "exe $tag: $(md5sum < $SRC/tests/fv3_ups_m17n_$tag.exe | cut -c1-12)"
done
cp $N/neg_tools/module_mp_thompson.F90.m17n2 $M
cd $B && OMP_NUM_THREADS=1 make -j 40 > $N/neg_tools/make_restore.log 2>&1; echo "restore rc=$? $(md5sum < $B/ufs_model | cut -c1-12) vs m17n2 $(md5sum < $SRC/tests/fv3_ups_m17n2.exe | cut -c1-12)"
echo "=== VARIANTS_EXIT ==="
