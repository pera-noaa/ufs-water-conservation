#!/bin/bash
# usage: mk_tree.sh <name> <src ufs-weather-model> [item ...]
#   item: x.py[:arg] (run on the tree), nofma (samfinit nofma.py), tm (tracer hook + tm meters + TX print)
# copies src (no .git/builds/exes/run dirs) to $L/<name>/ufs-weather-model
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; L=$U/cons/latent; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S=$U/cons/trsamf/bin
t=${1:?name}; SB=${2:?src}; shift 2
D=$L/$t/ufs-weather-model
[ -e "$L/$t" ] && { echo "ABORT $L/$t exists"; exit 1; }
mkdir -p "$D"
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$SB/" "$D/"
for it in "$@"; do
  case $it in
    nofma) $P -I $U/cons/samfinit/tools/nofma.py "$D";;
    tm) $P -I $S/testhook_chem_pbl.py "$D"; $P -I $S/instrument_tm.py "$D" $S/tm_meter.F90; $P -I $S/post_tx.py "$D";;
    *.py) $P -I $L/bin/$it "$D";;
    *.py:*) $P -I $L/bin/${it%%:*} "$D" ${it#*:};;
    *) echo "ABORT item $it"; exit 1;;
  esac
done
echo "TREE_OK $D"
