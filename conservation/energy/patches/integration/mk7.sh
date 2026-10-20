#!/bin/bash
# usage: nohup mk7.sh <src> <dst> & : copy, apply trdyn 02b, 03b, 01_DYN_v4 (-F0), re-anchor clashes (rebase_trdyn.py), build
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S=$E/${1:?src}; D=$E/${2:?dst}
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
cd $D/ufs-weather-model/UFSATM/ccpp/physics
patch -p1 -F0 < $E/accepted/16_trdyn_02b_T1_samf_tracer_substep.diff | grep -i -E "FAILED|reject" || true
patch -p1 -F0 < $E/accepted/17_trdyn_03b_DRY_chem_tracers_dry_mixing_ratio_transport.diff | grep -i -E "FAILED|reject" || true
cd $D/ufs-weather-model
patch -p1 -F0 < $E/accepted/18_trdyn_01_DYN_dry_tracer_adv_remap_ic_v4.diff | grep -i -E "FAILED|reject" || true
$P -I $E/tools/rebase_trdyn.py $D/ufs-weather-model || { echo "ABORT: rejects left"; exit 1; }
find $D/ufs-weather-model -name "*.orig" -newer $E/accepted/18_trdyn_01_DYN_dry_tracer_adv_remap_ic_v4.diff -delete
cd $E && sbatch -J e_$(basename $D) --export=NONE,SRC=$D/ufs-weather-model,CLEAN=YES build64.sbatch
