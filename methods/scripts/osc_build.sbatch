#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:00:00
# Build a wbosc* tree (full with MODE=full, else incremental make); exe -> $V/<T>/exe/fv3_<TAG>.exe.
# Usage: sbatch -J wb_osc_b<TAG> -o $V/<T>/logs/%x.%j.log --export=NONE,T=<T>,TAG=<TAG>[,MODE=full] osc_build.sbatch
V=/work2/noaa/co2/ash/ufs-chem-v1/variants
: "${T:?T not set}" "${TAG:?TAG not set}"
case "$T" in wbosc*) ;; *) echo "refusing tree $T"; exit 1;; esac
SRC=$V/$T/ufs_model.fd
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
t0=$(date +%s)
if [ "${MODE:-}" = full ]; then
  cd "$SRC/tests" && BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -D32BIT=ON" "herc_$T" intel YES NO
  RC=$?
  EXE=$SRC/tests/fv3_herc_$T.exe
else
  source /etc/profile >/dev/null 2>&1 || true
  module use "$SRC/modulefiles"
  module load ufs_hercules.intel
  cd "$SRC/tests/build_fv3_herc_$T" && OMP_NUM_THREADS=1 make -j 40 2>&1 | grep -v "^\[ *[0-9]*%\] Built target" | tail -30
  RC=${PIPESTATUS[0]}
  EXE=$SRC/tests/build_fv3_herc_$T/ufs_model
fi
if [ "$RC" = 0 ]; then
  cp "$EXE" "$V/$T/exe/fv3_${TAG}.exe"
  P=FV3/ccpp/physics/physics
  diff -ru -x "*.pre*" -x "*.orig" -x "*.meter*" -x "*.unmetered*" "$V/wbfinal/ufs_model.fd/$P" "$SRC/$P" > "$V/$T/exe/fv3_${TAG}.diff"
  echo "exe: $V/$T/exe/fv3_${TAG}.exe ($(md5sum < "$V/$T/exe/fv3_${TAG}.exe" | cut -c1-12))"
fi
echo "=== BUILD_EXIT rc=$RC seconds=$(( $(date +%s) - t0 )) ==="
