#!/bin/bash
# usage: nohup mk13.sh & : full13/mq13 = full12/mq12 + preclag 01_PL1 + suites 01 01b 02 03 04 05 06 07 08 (-p1 -F0; the
# switch hunks of 03/04/06 in GFS_typedefs.F90 sit next to canopy TH9's lines: rebase_r11.py REJ). ensfc2 16b = 16 + the
# integrator metadata fix already in full11 (content diff = that line). mq13: meter v2 probes regenerated (EB_PBLFLX EB_PH1
# EB_LAG) + preclag's meter_PL1_lag_v2.diff. Bug-fix arm gB13 = gB11 + suites 01 01b 02 05 07 08 (the unconditional ones);
# A/B arms gB13n05 (no 05), gB13n08 (no 08). All -no-fma (inherited). <= 2 own builds at a time.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; A=$E/accepted
TD=UFSATM/ccpp/data/GFS_typedefs.F90
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $1/ $2/; }
pp() {  # pp <tree> <n> [REJ] : -p1 -F0; rejects only where the REJ stage re-anchors them
  f=$(ls $A/${2}_*.diff); (cd $E/$1/ufs-weather-model && patch -p1 -F0 < $f | grep FAILED; true)
  echo "$1 $(basename $f) md5 $(md5sum < $f | cut -c1-12)"
  if [ -n "${3:-}" ]; then $P -I $E/tools/rebase_r11.py $E/$1/ufs-weather-model REJ ${TD#UFSATM/} || { echo "ABORT: REJ $2 on $1"; exit 1; }
  else [ -z "$(find $E/$1/ufs-weather-model -name '*.rej')" ] || { echo "ABORT: rejects after $2 on $1"; exit 1; }; fi; }
for pr in "full12 full13" "mq12 mq13"; do
  set -- $pr; cp_tree $E/$1 $E/$2; t=$2
  pp $t 41; pp $t 32; pp $t 33; pp $t 34; pp $t 35 REJ; pp $t 36 REJ; pp $t 37; pp $t 38 REJ; pp $t 39; pp $t 40
  find $E/$t/ufs-weather-model -name "*.orig" -newer $A/41_preclag_01_PL1_sfc_precip_t1_carry.diff -delete
  grep -c "no-fma" $E/$t/ufs-weather-model/cmake/IntelMixed.cmake
done
EB_PBLFLX=1 EB_PH1=1 EB_LAG=1 $P -I $E/tools/instrument_eb_phys2.py $E/mq13/ufs-weather-model || { echo "ABORT: meter"; exit 1; }
(cd $E/mq13/ufs-weather-model && patch -p1 -F0 -s < $E/tools/meter_PL1_lag_v2.diff) || { echo "ABORT: preclag meter on mq13"; exit 1; }; echo "mq13 meter_PL1_lag_v2"
for spec in "gB13:32 33 34 37 39 40" "gB13n05:32 33 34 39 40" "gB13n08:32 33 34 37 39"; do
  t=${spec%%:*}; cp_tree $E/gB11 $E/$t
  for n in ${spec#*:}; do pp $t $n; done
done
cd $E
sub() { sbatch -J e_$1 --export=NONE,SRC=$E/$1/ufs-weather-model,CLEAN=YES build64.sbatch; }
wait2() { sleep 30; while [ "$(squeue -h -n e_full13,e_mq13,e_gB13,e_gB13n05,e_gB13n08 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done; }
sub full13; sub mq13; wait2; sub gB13; wait2; sub gB13n05; wait2; sub gB13n08
echo "TREES SUBMITTED"
