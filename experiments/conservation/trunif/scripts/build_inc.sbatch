#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --exclusive -t 00:30:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trunif/logs/inc_%x.%j.log
# usage: sbatch -J <id> --export=NONE,SRC=<tree>[,RECONF=1] build_inc.sbatch (RECONF reruns cmake, needed after .meta changes) ; incremental make in SRC/tests/build_fv3_<id>, exe -> SRC/tests/fv3_<id>.exe
set -x
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -i conda | paste -sd:)
unset PYTHONPATH
type module >/dev/null 2>&1 || source /apps/other/lmod/lmod/init/bash
module use "$SRC/modulefiles"
module load ufs_hercules.intel
B="$SRC/tests/build_fv3_${SLURM_JOB_NAME}"
cd "$B" || exit 3
date -Is
if [ -n "${RECONF:-}" ]; then cmake . > "$B/reconf.log" 2>&1 || { echo RECONF_FAILED; exit 4; }; fi
make -j 40 > "$B/inc_make.log" 2>&1
RC=$?
tail -5 "$B/inc_make.log"; grep -m5 -i "error" "$B/inc_make.log"
[ $RC -eq 0 ] && cp -p "$B/ufs_model" "$SRC/tests/fv3_${SLURM_JOB_NAME}.exe"
date -Is
echo "=== BUILD_EXIT rc=$RC ==="
