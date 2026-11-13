#!/bin/bash
#SBATCH -A co2 -p hercules -N 1 --exclusive -t 00:20:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/variants/wbgc/logs/build_%x.%j.log
# Incremental rebuild of the wbgc tree (copy of wbdev/build_inc.sbatch): sbatch -q batch -J inc_<TAG> --export=NONE,TAG=<TAG> gc_build_inc.sbatch
V=/work2/noaa/co2/ash/ufs-chem-v1/variants
W=$V/wbgc
SRC=$W/ufs_model.fd
B=$SRC/tests/build_fv3_herc_wbgc
: "${TAG:?TAG not set}"
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
exec 9>"$W/build.lock"
flock -w 600 9 || { echo "=== INC_BUILD_EXIT rc=99 (lock) ==="; exit 99; }
source /etc/profile >/dev/null 2>&1 || true
module use "$SRC/modulefiles"
module load ufs_hercules.intel
t0=$(date +%s)
cd "$B" && OMP_NUM_THREADS=1 make -j 40 2>&1 | grep -v "^\[ *[0-9]*%\] Built target" | tail -40
RC=${PIPESTATUS[0]}
if [ "$RC" = 0 ]; then
  cp "$B/ufs_model" "$W/exe/fv3_${TAG}.exe"
  P=FV3/ccpp/physics/physics
  diff -ru "$V/wbdev/ufs_model.fd/$P" "$SRC/$P" > "$W/exe/fv3_${TAG}.diff"
  echo "exe: $W/exe/fv3_${TAG}.exe ($(md5sum < "$W/exe/fv3_${TAG}.exe" | cut -c1-12)); diff vs wbdev: $(grep -c '^[-+][^-+]' "$W/exe/fv3_${TAG}.diff") changed lines"
fi
echo "=== INC_BUILD_EXIT rc=$RC seconds=$(( $(date +%s) - t0 )) ==="
