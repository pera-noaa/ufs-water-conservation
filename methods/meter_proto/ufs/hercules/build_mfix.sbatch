#!/bin/bash
#SBATCH -J mp_build_fix
#SBATCH -A co2
#SBATCH -p hercules
#SBATCH -q batch
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH -t 03:00:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/logs/build_mfix.%j.log
set -x
export MACHINE_ID=hercules
export PATH=$(echo $PATH | tr : "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
cd /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/src_fix/tests
export BUILD_JOBS=40
date -Is
./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v16,FV3_GFS_v17_p8,FV3_GFS_v17_p8_rrtmgp,FV3_GFS_v15_thompson_mynn_lam3km,FV3_WoFS_v0,FV3_GFS_v17_p8_mynn,FV3_GFS_v17_p8_ugwpv1,FV3_GFS_v16_gfdlmpv3,FV3_GFS_v17_p8_ugwpv1_tempo,FV3_WoFS_v0_tempo -D32BIT=ON" mpfix intel YES NO
echo "BUILD_RC=$? $(date -Is)"
ls -l fv3_mpfix.exe
