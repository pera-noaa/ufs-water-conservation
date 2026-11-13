#!/bin/bash
# usage: nohup mkfix.sh <src tree> <dst tree> <fix id> [...] & : copy a tree, apply fixes (tools/apply_fixes_r4.py), build
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S=$E/${1:?src}; D=$E/${2:?dst}; shift 2
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
$P -I $E/tools/apply_fixes_r4.py $D/ufs-weather-model "$@"
cd $E && sbatch -J e_$(basename $D) --export=NONE,SRC=$D/ufs-weather-model,CLEAN=YES build64.sbatch
