#!/bin/bash
# usage: [PRE="root.diff ..."] [PHYS="02b_T1 03b_DRY"] [METER=0] mk_tree.sh <name> [fix.diff ...] : $W/<name> = tracer base + physics patches
# (default trsamf 02 + 03, in UFSATM/ccpp/physics) + fix diffs (tree root, -p1) + test hook (chem tracers PBL-mixed)
# + (METER=1, default) tm meters, env-switchable uniform reset, trunif shadow meter
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trdyn; T=$U/cons/tracer; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
t=${1:?name}; shift
[ -e "$W/$t" ] && { echo "ABORT $W/$t exists"; exit 1; }
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$T/base/" "$W/$t/"
for d in ${PRE:-}; do (cd "$W/$t" && patch -p1 --forward --no-backup-if-mismatch -F0 < "$d"); done
for p in ${PHYS:-02_T1 03_DRY}; do (cd "$W/$t/UFSATM/ccpp/physics" && patch -p1 --forward --no-backup-if-mismatch -F0 < $W/patches/${p}_*.diff); done
for d in "$@"; do (cd "$W/$t" && patch -p1 --forward --no-backup-if-mismatch -F0 < "$d"); done
$P -I $W/bin/testhook_chem_pbl.py "$W/$t"
if [ "${METER:-1}" = 1 ]; then
  $P -I $W/bin/instrument_tm.py "$W/$t" $W/bin/tm_meter.F90
  $P -I $W/bin/testhook_uniform_reset_env.py "$W/$t"
  $P -I $W/bin/instrument_shadow.py "$W/$t" $W/bin/tm_shadow.inc
fi
echo "TREE_OK $W/$t"
