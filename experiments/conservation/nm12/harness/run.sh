#!/bin/bash
# usage: run.sh <name> <variants> <namelist body>   e.g. run.sh built720 "orig fix neg pristine" "mode='single' kind='built' ncol=100000 dt=720."
N=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12
name=$1; vars=$2; nml=$3
module purge >/dev/null 2>&1
module use /work2/noaa/co2/ash/ufs-chem-v1/upstream/p20rt_final/ufs-weather-model/modulefiles
module load ufs_hercules.intel >/dev/null 2>&1
ulimit -s unlimited
D=$N/runs/$name; mkdir -p $D; cd $D
cp -p $N/src/noahmptable.tbl .
for v in $vars; do
  echo "&nm12 $nml out='$v' /" > nml_$v
  /usr/bin/time -f "$v %e s" $N/build/$v/nm12_$v.x < nml_$v > $v.log 2>&1
  echo "== $name $v"; tail -6 $v.log
done
