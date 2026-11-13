#!/bin/bash
# Make a work tree in $W from a source tree: copy (no .git/builds/exes), apply pre items (*.diff in UFSATM/ccpp/physics
# with patch -p1, or *.py <tree>), then hook + meters + uniform reset + TX print, then post:<script.py> items.
# usage: mk_tree.sh <name> <src tree> [item ...]   (item: x.diff | x.py | post:x.py)
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trsamf; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
t=${1:?name}; SB=${2:?src}; shift 2
[ -e "$W/$t" ] && { echo "ABORT $W/$t exists"; exit 1; }
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$SB/" "$W/$t/"
post=()
for f in "$@"; do
  case $f in
    post:*) post+=("${f#post:}");;
    *.diff) (cd "$W/$t/UFSATM/ccpp/physics" && patch -p1 --forward --no-backup-if-mismatch < "$f");;
    *.py) $P -I "$f" "$W/$t";;
    *) echo "ABORT item $f"; exit 1;;
  esac
done
$P -I $W/bin/testhook_chem_pbl.py "$W/$t"
$P -I $W/bin/instrument_tm.py "$W/$t" $W/bin/tm_meter.F90
$P -I $W/bin/testhook_uniform_reset.py "$W/$t"
$P -I $W/bin/post_tx.py "$W/$t"
for f in "${post[@]}"; do $P -I "$f" "$W/$t"; done
echo "TREE_OK $W/$t"
