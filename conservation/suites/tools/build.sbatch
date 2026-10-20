#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 01:10:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/logs/build_%x.%j.log
# usage: sbatch -J <tag> --export=NONE,TREES="<tree> [<tree>]" build.sbatch
#   builds each $S/<tree>/ufs-weather-model (in parallel), APP=ATM, 64-bit dycore, the three suites; exe -> $S/exe/<tree>.exe
set -x
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
mkdir -p $S/exe
n=$(echo $TREES | wc -w); bj=$((76 / n))
for t in $TREES; do
  ( cd $S/$t/ufs-weather-model/tests && BUILD_JOBS=$bj ./compile.sh hercules \
      "-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_mynn,FV3_GFS_v16_gfdlmpv3,FV3_RAP" "s_$t" intel ${CLEAN:-YES} NO \
      > $S/logs/compile_$t.log 2>&1
    rc=$?; echo "=== BUILD $t rc=$rc"
    cp -p $S/$t/ufs-weather-model/tests/fv3_s_$t.exe $S/exe/$t.exe && md5sum $S/exe/$t.exe ) &
done
wait
date -Is
echo "=== BUILD_DONE"
