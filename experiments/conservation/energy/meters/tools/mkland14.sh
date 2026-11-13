#!/bin/bash
# usage: nohup mkland14.sh & : NM10r phase-agreement diagnostic (after final14): mq14b = mq14 + instrument_land14b.py
# (thresholds, max relative difference, Noah-MP prcp vs host P); mq14bn = mq14b with NM10r reverted (PH2 gated on
# precip_phase_host again: NM10's sfctmp rule when off) = the known-bad control. Both run all-off.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
out=$E/logs/land14.txt; : > $out; cd $E
until grep -q -E "FINAL14 DONE|ABORT" logs/final14.txt; do sleep 60; done
for t in mq14b mq14bn; do d=$E/$t; [ -e $d ] && { echo "ABORT: $t exists" >> $out; exit 1; }
  rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/mq14/ $d/
  $P -I $E/tools/instrument_land14b.py $d/ufs-weather-model >> $out 2>&1 || { echo "ABORT: land14b $t" >> $out; exit 1; }; done
f=$E/mq14bn/ufs-weather-model/UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/noahmpdrv.F90
[ "$(grep -c '        if (precip_convective > 0.) then' $f)" = 1 ] || { echo "ABORT: bn anchor" >> $out; exit 1; }
sed -i 's/^        if (precip_convective > 0.) then$/        if (pph .and. precip_convective > 0.) then/' $f; echo "mq14bn: NM10r reverted (pph gate)" >> $out
a=$(sbatch -J e_mq14b --export=NONE,SRC=$E/mq14b/ufs-weather-model,CLEAN=YES build64.sbatch | awk '{print $NF}')
b=$(sbatch -J e_mq14bn --export=NONE,SRC=$E/mq14bn/ufs-weather-model,CLEAN=YES build64.sbatch | awk '{print $NF}')
while squeue -h -j $a,$b 2>/dev/null | grep -q .; do sleep 60; done
for t in mq14b mq14bn; do cp $t/ufs-weather-model/tests/fv3_e_$t.exe exe/ || { echo "ABORT: build $t" >> $out; exit 1; }; done
a=$(./mkrun.sh m14b_off exe/fv3_e_mq14b.exe | awk '{print $NF}'); b=$(./mkrun.sh m14bn_off exe/fv3_e_mq14bn.exe | awk '{print $NF}')
echo "m14b_off $a m14bn_off $b" >> $out
while squeue -h -j $a,$b 2>/dev/null | grep -q .; do sleep 60; done
cd runs; for t in m14b_off m14bn_off; do echo "=== $t" >> $out; $P -I ../tools/land14_table.py $t/out >> $out 2>&1; done
echo "-- m14b_off (NM10r) vs m14_off: $($P -I ../tools/cmp_allvars.py m14_off m14b_off sfcf024 1 2>&1 | head -1)" >> $out
echo LAND14 DONE >> $out
