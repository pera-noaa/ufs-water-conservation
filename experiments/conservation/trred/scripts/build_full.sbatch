#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 00:50:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trred/logs/build_%x.%j.log
# usage: sbatch -J <id> --export=NONE,SRC=<tree>,SUITES=<a,b>[,XOPT=-DSAMFCNV_32BIT=ON] build_full.sbatch ; exe -> SRC/tests/fv3_<id>.exe
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
cd "${SRC}/tests"
date -Is
BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=${SUITES} ${XOPT:-}" "${SLURM_JOB_NAME}" intel NO NO
RC=$?
date -Is
ls -la ${SRC}/tests/fv3_${SLURM_JOB_NAME}.exe
echo "=== BUILD_EXIT rc=$RC ==="
