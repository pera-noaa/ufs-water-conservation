#!/bin/bash
#SBATCH -J mp_stage_th
#SBATCH -A co2
#SBATCH -p hercules
#SBATCH -q batch
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH -t 00:10:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/logs/stage_mth.%j.log
M=/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto
cd $M && bash stage_run.sh mth_on $M/src_th/tests/fv3_mpfix.exe $M/src_th/tests/modules.fv3_mpfix.lua T T
