#!/bin/bash
# usage: mkdiffs.sh <base tree> <outdir> <num>:<FIX>:<name> ... ; one diff per fix, each applied alone on <base tree>
# (and on top of the previous ones in the list, so the series applies in order)
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
B=$E/${1:?base}; O=$E/${2:?outdir}; shift 2
T=$E/scratch_diffs; rm -rf "${T:?}"; mkdir -p $T/a/UFSATM/fv3 $O
cp -r $B/ufs-weather-model/UFSATM/ccpp $T/a/UFSATM/; cp -r $B/ufs-weather-model/UFSATM/fv3/atmos_cubed_sphere $T/a/UFSATM/fv3/
for item in "$@"; do
  n=${item%%:*}; r=${item#*:}; fx=${r%%:*}; name=${r#*:}
  rm -rf "${T:?}/b"; cp -r $T/a $T/b
  $P -I $E/tools/apply_fixes_r4.py $T/b $fx > /dev/null
  (cd $T && diff -ruN a b > $O/${n}_${name}.diff) || true
  echo "$n $fx $(grep -c '^[+-][^+-]' $O/${n}_${name}.diff) lines"
  rm -rf "${T:?}/a"; mv $T/b $T/a
done
rm -rf "${T:?}"
