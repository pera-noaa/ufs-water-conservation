#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:30:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent/logs/buildn_%x.%j.log
# usage: sbatch -J <id> --export=NONE,TREES="t3 mt3 s32 ms32:-DSAMFCNV_32BIT=ON",BJ=20 buildn.sbatch
# builds $L/<t>/ufs-weather-model side by side on one node; exe -> tests/fv3_<t>.exe
L=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
date -Is
for it in $TREES; do
  t=${it%%:*}; x=""; [ "$it" != "$t" ] && x=${it#*:}
  (cd $L/$t/ufs-weather-model/tests && BUILD_JOBS=${BJ:-20} ./compile.sh hercules "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 $x" $t intel YES NO > $L/logs/compile_$t.log 2>&1; echo "=== BUILD_EXIT $t rc=$? $(ls fv3_$t.exe 2>&1)") &
  sleep 5
done
wait
date -Is
