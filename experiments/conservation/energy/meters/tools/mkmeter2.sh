#!/bin/bash
# usage: nohup mkmeter2.sh <src tree> <dst tree> [extra fix ids for apply_fixes_r4.py] & : copy, regenerate CCPP probes (meter v2), build
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S=$E/${1:?src}; D=$E/${2:?dst}; shift 2
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
$P -I $E/tools/instrument_eb_phys2.py $D/ufs-weather-model
for f in "$@"; do $P -I $E/tools/apply_fixes_r4.py $D/ufs-weather-model $f; done
cd $E && sbatch -J e_$(basename $D) --export=NONE,SRC=$D/ufs-weather-model,CLEAN=YES build64.sbatch
