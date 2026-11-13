#!/bin/bash
# mkfx2.sh : v2 fix. fx2 = gA + v2 ; mfx2 = fx2 + meter ; hyd2 / mg2 = fx2 built -DHYDRO=ON / -DMULTI_GASES=ON (compile checks)
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; F=$U/cons/fv3tally; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
D=$F/patches/01_fv3-dyn_te_exact.v2.diff
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" --exclude="ufs-weather-model/tests/*.log" $1/ $2/; }
for t in fx2 mfx2 hyd2 mg2; do
  cp_tree $E/gA $F/$t || exit 1
  (cd $F/$t/ufs-weather-model && patch -p1 -F0 -s < $D) || { echo "ABORT: v2 on $t"; exit 1; }
  echo "$t: v2 applied"
done
$P -I $F/meters/instrument_tally.py $F/mfx2/ufs-weather-model $F/meters/fv_etally.F90 || exit 1
cd $F/tools
mine=""
slot() { while :; do n=0; for j in ${mine//,/ }; do squeue -h -j $j 2>/dev/null | grep -q . && n=$((n+1)); done; [ $n -lt 2 ] && return; sleep 30; done; }
for t in fx2 mfx2 hyd2 mg2; do
  x=""; [ $t = hyd2 ] && x="-DHYDRO=ON"; [ $t = mg2 ] && x="-DMULTI_GASES=ON"
  slot; j=$(sbatch --parsable -J t_$t --export=NONE,SRC=$F/$t/ufs-weather-model,CLEAN=YES,EXTRA="$x" build64.sbatch); mine="$mine,$j"; echo "$(date +%T) t_$t $j"
done
