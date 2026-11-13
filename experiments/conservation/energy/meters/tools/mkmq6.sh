#!/bin/bash
# usage: nohup mkmq6.sh <src metered> <dst metered> <src plain> <dst plain> & : apply PBF to both, regenerate meter v2 probes
# with the PBL condensate fluxes (EB_PBLFLX=1) in the metered copy, build both
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
SM=$E/$1; DM=$E/$2; SP=$E/$3; DP=$E/$4
for d in $DM $DP; do [ -e "$d" ] && { echo "ABORT: $d exists"; exit 1; }; done
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $SM/ $DM/
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $SP/ $DP/
$P -I $E/tools/apply_fixes_r4.py $DM/ufs-weather-model PBF
$P -I $E/tools/apply_fixes_r4.py $DP/ufs-weather-model PBF
EB_PBLFLX=1 $P -I $E/tools/instrument_eb_phys2.py $DM/ufs-weather-model
cd $E
sbatch -J e_$(basename $DM) --export=NONE,SRC=$DM/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_$(basename $DP) --export=NONE,SRC=$DP/ufs-weather-model,CLEAN=YES build64.sbatch
