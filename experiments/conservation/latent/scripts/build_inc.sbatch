#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 00:40:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent/logs/inc_%x.%j.log
# usage: sbatch -J <id> --export=NONE,TREES="t3 mt3" build_inc.sbatch ; make in $L/<t>/ufs-weather-model/tests/build_fv3_<t>, exe -> tests/fv3_<t>.exe
L=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
type module >/dev/null 2>&1 || source /apps/other/lmod/lmod/init/bash
for t in $TREES; do
  (S=$L/$t/ufs-weather-model; module use "$S/modulefiles"; module load ufs_hercules.intel
   cd $S/tests/build_fv3_$t && make -j 40 > inc_make.log 2>&1; rc=$?
   [ $rc -eq 0 ] && cp -p ufs_model $S/tests/fv3_$t.exe
   echo "=== BUILD_EXIT $t rc=$rc"; grep -m3 -i " error" inc_make.log) &
done
wait
