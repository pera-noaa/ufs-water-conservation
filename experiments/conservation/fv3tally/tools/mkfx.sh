#!/bin/bash
# mkfx.sh : fx = gA (full10, -no-fma) + 01_fv3-dyn_te_exact ; mfx = fx + tally meter ; submit both builds
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; F=$U/cons/fv3tally; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" --exclude="ufs-weather-model/tests/*.log" $1/ $2/; }
for t in fx mfx; do
  cp_tree $E/gA $F/$t || exit 1
  # patch writes new files (no write through links): check the targets are regular files
  for f in dyn_core sw_core fv_dynamics fv_arrays fv_control fv_mapz; do
    [ -L $F/$t/ufs-weather-model/UFSATM/fv3/atmos_cubed_sphere/model/$f.F90 ] && { echo "ABORT: $f is a link"; exit 1; }
  done
  (cd $F/$t/ufs-weather-model && patch -p1 -F0 -s < $F/patches/01_fv3-dyn_te_exact.diff) || { echo "ABORT: fix on $t"; exit 1; }
  echo "$t: fix applied"
done
$P -I $F/meters/instrument_tally.py $F/mfx/ufs-weather-model $F/meters/fv_etally.F90 || exit 1
cd $F/tools
sbatch -J t_fx  --export=NONE,SRC=$F/fx/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J t_mfx --export=NONE,SRC=$F/mfx/ufs-weather-model,CLEAN=YES build64.sbatch
