#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:45:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/samfinit/logs/build_%x.%j.log
# usage: sbatch -J <name> --export=NONE,FROM=<src ufs-weather-model>,DST=<new dir>,DBG=ON|OFF build_dbg.sbatch
# HOOKS: space-separated tools/*.py run on the copied tree
# copies FROM (no build dirs) to DST/ufs-weather-model unless it exists, then builds ATM p8_ugwpv1, 64-bit, DEBUG=$DBG
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
S=${DST:?}/ufs-weather-model
if [ ! -d "$S" ]; then
  mkdir -p "$DST"
  rsync -a --exclude="tests/build_fv3_*" --exclude="tests/fv3_*.exe" --exclude="tests/logs" "${FROM:?}/" "$S/" || exit 1
  for h in ${HOOKS:-}; do /work2/noaa/co2/miniconda3/envs/tm5/bin/python -I /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/samfinit/tools/$h "$S" || exit 1; done
fi
cd "$S/tests"
date -Is
BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -DDEBUG=${DBG:-ON}" "${SLURM_JOB_NAME}" intel ${CLEAN:-YES} NO
RC=$?
date -Is
echo "=== BUILD_EXIT rc=$RC ==="
