#!/bin/bash
#SBATCH -A co2 -p hercules -N 1 --exclusive -t 00:30:00
# Incremental rebuild of $V/<T> (T = wbka*) after a full build_variant.sbatch build; exe -> $V/<T>/exe/fv3_<TAG>.exe with the
# physics diff against wbfinal. Usage: sbatch -q batch -J inc_<TAG> -o $V/<T>/logs/%x.%j.log --export=NONE,T=<T>,TAG=<TAG> this
V=/work2/noaa/co2/ash/ufs-chem-v1/variants
: "${T:?T not set}" "${TAG:?TAG not set}"
case "$T" in wbka*) ;; *) echo "refusing tree $T"; exit 1;; esac
SRC=$V/$T/ufs_model.fd
B=$SRC/tests/build_fv3_herc_$T
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
source /etc/profile >/dev/null 2>&1 || true
module use "$SRC/modulefiles"
module load ufs_hercules.intel
t0=$(date +%s)
cd "$B" && OMP_NUM_THREADS=1 make -j 40 2>&1 | grep -v "^\[ *[0-9]*%\] Built target" | tail -30
RC=${PIPESTATUS[0]}
if [ "$RC" = 0 ]; then
  mkdir -p "$V/$T/exe"
  cp "$B/ufs_model" "$V/$T/exe/fv3_${TAG}.exe"
  P=FV3/ccpp/physics/physics
  diff -ru -x "*.pre*" -x "*.orig" "$V/wbfinal/ufs_model.fd/$P" "$SRC/$P" > "$V/$T/exe/fv3_${TAG}.diff"
  echo "exe: $V/$T/exe/fv3_${TAG}.exe ($(md5sum < "$V/$T/exe/fv3_${TAG}.exe" | cut -c1-12))"
fi
echo "=== INC_BUILD_EXIT rc=$RC seconds=$(( $(date +%s) - t0 )) ==="
