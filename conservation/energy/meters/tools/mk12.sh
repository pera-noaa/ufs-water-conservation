#!/bin/bash
# usage: nohup mk12.sh & : full12/mq12 = full11/mq11 + fv3tally 01_fv3-dyn_te_exact.v2 (-p1 -F0; mq: fv_dynamics hunks 1-2
# re-anchored next to the dycore meter probe by rebase_r11.py DTE); -no-fma inherited; build both
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons; A=$E/accepted; D=$A/31_fv3tally_01_fv3-dyn_te_exact_v2.diff
cp -p $U/fv3tally/patches/01_fv3-dyn_te_exact.v2.diff $D
for pr in "full11 full12" "mq11 mq12"; do
  set -- $pr; [ -e "$E/$2" ] && { echo "ABORT: $2 exists"; exit 1; }
  rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/$1/ $E/$2/
  (cd $E/$2/ufs-weather-model && patch -p1 -F0 < $D | grep FAILED; true); echo "$2 $(basename $D) md5 $(md5sum < $D | cut -c1-12)"
  $P -I $E/tools/rebase_r11.py $E/$2/ufs-weather-model DTE $D || { echo "ABORT: DTE on $2"; exit 1; }
  find $E/$2/ufs-weather-model -name "*.orig" -newer $D -delete
  grep -c "no-fma" $E/$2/ufs-weather-model/cmake/IntelMixed.cmake
done
F=UFSATM/fv3/atmos_cubed_sphere/model; for f in dyn_core.F90 fv_arrays.F90 fv_control.F90 fv_mapz.F90 sw_core.F90 fv_dynamics.F90; do
  echo "$f full12-vs-mq12 extra lines: $(diff $E/full12/ufs-weather-model/$F/$f $E/mq12/ufs-weather-model/$F/$f | grep -c '^>') (mq11 vs full11: $(diff $E/full11/ufs-weather-model/$F/$f $E/mq11/ufs-weather-model/$F/$f | grep -c '^>'))"; done
cd $E
sbatch -J e_full12 --export=NONE,SRC=$E/full12/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_mq12 --export=NONE,SRC=$E/mq12/ufs-weather-model,CLEAN=YES build64.sbatch
echo "TREES SUBMITTED"
