#!/bin/bash
# mkmt.sh : mt = gA (full10, -no-fma) + tally meter ; mt0 = base (ctl64 source, release) + tally meter ; submit both builds
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; F=$U/cons/fv3tally; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
mkdir -p $F/logs $F/exe $F/runs
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" --exclude="ufs-weather-model/tests/*.log" $1/ $2/; }
cp_tree $E/gA $F/mt  || exit 1
cp_tree $E/base $F/mt0 || exit 1
$P -I $F/meters/instrument_tally.py $F/mt/ufs-weather-model  $F/meters/fv_etally.F90 || exit 1
$P -I $F/meters/instrument_tally.py $F/mt0/ufs-weather-model $F/meters/fv_etally.F90 || exit 1
cd $F/tools
sbatch -J t_mt  --export=NONE,SRC=$F/mt/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J t_mt0 --export=NONE,SRC=$F/mt0/ufs-weather-model,CLEAN=YES build64.sbatch
