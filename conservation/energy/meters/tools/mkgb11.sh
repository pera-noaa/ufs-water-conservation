#!/bin/bash
# usage: nohup mkgb11.sh & : gB11 = gB (fx + switchless bug fixes, -no-fma) + ensfc2 13 14 15 + TH9 via canopy's anchor tool
# apply_th9.py (canopy's 03 diff is cut on full10's Thompson text and does not apply to fx). Submits after full11/mq11 builds.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons; A=$E/accepted
d=$E/gB11; rm -rf "${d:?}"
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/gB/ $E/gB11/
for f in 24_ensfc2_13_sfc_SL2 25_ensfc2_14_sfc_CS1 26_ensfc2_15_sfc_CB1; do
  (cd $E/gB11/ufs-weather-model && patch -p2 -F0 -s < $A/$f.diff) || { echo "ABORT: $f on gB11"; exit 1; }; echo "gB11 $f"; done
cp -p $U/canopy/tools/apply_th9.py $E/tools/canopy_apply_th9.py
$P -I $E/tools/canopy_apply_th9.py $E/gB11/ufs-weather-model || { echo "ABORT: apply_th9 on gB11"; exit 1; }; echo "gB11 TH9 (apply_th9.py)"
[ -z "$(find $E/gB11/ufs-weather-model -name '*.rej')" ] || { echo "ABORT: rej in gB11"; exit 1; }
grep -c "no-fma" $E/gB11/ufs-weather-model/cmake/IntelMixed.cmake
cd $E
while [ "$(squeue -h -n e_full11,e_mq11 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done
sbatch -J e_gB11 --export=NONE,SRC=$E/gB11/ufs-weather-model,CLEAN=YES build64.sbatch
echo "TREES SUBMITTED"
