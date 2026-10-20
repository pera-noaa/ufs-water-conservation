#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:30:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn/logs/build_%x.%j.log
# usage: sbatch -J <id> --export=NONE,SRC=<tree>[,OPTS="-D32BIT=ON"][,SUITES=a:b] build_full.sbatch (sbatch --export
# splits on commas, so suites are colon-separated here)
# default: APP=ATM, p8_ugwpv1 suite, 64-bit dycore
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
SUITES=${SUITES:-FV3_GFS_v17_p8_ugwpv1}
cd "${SRC}/tests"
date -Is
BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM ${OPTS:-} -DCCPP_SUITES=${SUITES//:/,}" "${SLURM_JOB_NAME}" intel NO NO
RC=$?
date -Is
echo "=== BUILD_EXIT rc=$RC ==="
