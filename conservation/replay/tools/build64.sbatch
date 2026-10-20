#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 00:40:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay/logs/build_%x.%j.log
# usage: sbatch -J <name> --export=NONE,SRC=<ufs-weather-model> build64.sbatch ; APP=ATM, p8_ugwpv1 suite, 64-bit dycore (no -D32BIT)
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
cd "${SRC}/tests"
date -Is
BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1" "${SLURM_JOB_NAME}" intel ${CLEAN:-YES} NO
RC=$?
date -Is
echo "=== BUILD_EXIT rc=$RC ==="
