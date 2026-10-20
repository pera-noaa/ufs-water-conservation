#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:10:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trred/logs/build2_%x.%j.log
# two builds side by side on one node: b32 (SAMFCNV_32BIT, p8_ugwpv1) and bsu (64-bit, p8_ugwpv1 + v17_p8)
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trred
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
date -Is
(cd $W/b32/tests && BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -DSAMFCNV_32BIT=ON" b32 intel NO NO > $W/logs/compile_b32.log 2>&1; echo "=== BUILD_EXIT b32 rc=$?") &
(cd $W/bsu/tests && BUILD_JOBS=40 ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1,FV3_GFS_v17_p8" bsu intel NO NO > $W/logs/compile_bsu.log 2>&1; echo "=== BUILD_EXIT bsu rc=$?") &
wait
date -Is
ls -la $W/b32/tests/fv3_b32.exe $W/bsu/tests/fv3_bsu.exe
