#!/bin/bash
# Re-create a work tree from base (keeping its build dir) and re-apply hook, meters and listed fix scripts.
# usage: [SRCBASE=<tree>] retool.sh <tree name> [fix.py ...]   (fix scripts take the tree path as $1); default base $T/base
set -euo pipefail
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
t=${1:?tree}; shift
SB=${SRCBASE:-$T/base}
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$SB/" "$T/$t/"
$P -I $T/bin/testhook_chem_pbl.py "$T/$t"
$P -I $T/bin/instrument_tm.py "$T/$t" $T/bin/tm_meter.F90
$P -I $T/bin/testhook_uniform_reset.py "$T/$t"
for f in "$@"; do $P -I "$f" "$T/$t"; done
