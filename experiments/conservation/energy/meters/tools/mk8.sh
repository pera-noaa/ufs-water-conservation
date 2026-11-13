#!/bin/bash
# usage: nohup mk8.sh & : full8/mq8 = full7/mq7 + ensfc2 04 05 06 08 09 10 11 (-p2 -F0); meter v2 probes regenerated
# in mq8 with PBL condensate fluxes and PH1 convective snow (EB_PBLFLX=1 EB_PH1=1); build both
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
P2=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/patches
for pr in "full7 full8" "mq7 mq8"; do
  set -- $pr; S=$E/$1; D=$E/$2
  [ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
  rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
  cd $D/ufs-weather-model
  for f in 04_sfc_SI1 05_sfc_SI2 06_sfc_NP1 08_sfc_QR1 09_sfc_CMC 10_sfc_FL1 11_sfc_options; do
    patch -p2 -F0 -s < $P2/$f.diff || { echo "ABORT: $f on $D"; exit 1; }
    echo "$D $f $(md5sum < $P2/$f.diff | cut -c1-12)"
  done
done
EB_PBLFLX=1 EB_PH1=1 $P -I $E/tools/instrument_eb_phys2.py $E/mq8/ufs-weather-model
cd $E
sbatch -J e_mq8 --export=NONE,SRC=$E/mq8/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_full8 --export=NONE,SRC=$E/full8/ufs-weather-model,CLEAN=YES build64.sbatch
