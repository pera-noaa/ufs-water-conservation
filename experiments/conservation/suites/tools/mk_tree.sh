#!/bin/bash
# usage: mk_tree.sh <tree> [meter] [fix...] : $S/<tree> = base (full10 copy) + -no-fma [+ suites meter] [+ fix diffs from $S/fixes]
set -euo pipefail
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
t=${1:?tree}; shift
D=$S/$t
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
rsync -a $S/base/ $D/
W=$D/ufs-weather-model
$PY $S/tools/nofma.py $W
for x in "$@"; do
  if [ "$x" = meter ]; then $PY $S/tools/instrument_sm.py $W
  else (cd $W && patch -p1 -F0 -s --no-backup-if-mismatch < $S/fixes/$x.diff) && echo "fix $x applied"; fi
done
echo "tree $t ready: $*"
