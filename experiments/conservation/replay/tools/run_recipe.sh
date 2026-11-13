#!/bin/bash
# usage: run_recipe.sh <recipe> <tree> [from_NN] : run each recipe line through step.sh; lines:
#   <NN_label> <method> <args...>   (see step.sh; $E, $A, $S2, $SRC, $TL expanded)
#   CMP <integrator tree>           compare the 60 changed files with an integrator stage tree
# stops at the first failure
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay
R=$R; E=$R/../energy; A=$E/accepted; S2=$R/../ensfc2/patches; SRC=$R/src; TL=$R/tools/energy_tools
P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
T=${2:?tree}; from=${3:-}; go=1; [ -n "$from" ] && go=0
while read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  line=$(eval echo "$line")
  set -- $line
  [ $go = 0 ] && { [ "$1" = "$from" ] && go=1 || continue; }
  if [ "$1" = CMP ]; then echo "CMP vs $2:"; $R/tools/cmp60.sh "$T" "$2"; continue; fi
  $R/tools/step.sh "$T" "$@" || exit 1
done < "${1:?recipe}"
