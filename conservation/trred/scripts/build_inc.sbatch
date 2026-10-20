#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 00:30:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trred/logs/inc_%x.%j.log
# usage: sbatch -J <id> --export=NONE,SRC=<tree>,B=<build dir name> build_inc.sbatch ; exe -> SRC/tests/fv3_<id>.exe
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
type module >/dev/null 2>&1 || source /apps/other/lmod/lmod/init/bash
module use "$SRC/modulefiles"
module load ufs_hercules.intel
cd "$SRC/tests/$B" || exit 3
make -j 40 > inc_make.log 2>&1
RC=$?
tail -3 inc_make.log; grep -m5 -i " error" inc_make.log
[ $RC -eq 0 ] && cp -p ufs_model "$SRC/tests/fv3_${SLURM_JOB_NAME}.exe"
echo "=== BUILD_EXIT rc=$RC ==="
