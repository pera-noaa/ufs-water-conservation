#!/bin/bash
# usage: integrate.sh <tag> <patch|FIX:<id>> [...]   (FIX:<id> = tools/apply_fixes_r3.py <tree> <id>, anchor based)
# Builds $E/all_<tag> = fx + R1 + patches (in order) and its metered twin $E/mall_<tag> = mfx + R1 + patches.
# Each patch is a unified diff meant for $E/fx (paths a/..., b/..., ufs-weather-model/..., or absolute); the -p level
# is found by dry run on the plain tree and must also apply cleanly (no fuzz) on the metered tree. Submits both builds.
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
tag=${1:?tag}; shift
A=$E/all_$tag; M=$E/mall_$tag
for d in $A $M; do [ -e "$d" ] && { echo "ABORT: $d exists"; exit 1; }; done
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/fx/ $A/
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/mfx/ $M/
for d in $A $M; do $P -I $E/tools/apply_fixes_r2.py $d/ufs-weather-model R1 >/dev/null; done
log=$E/logs/integrate_$tag.txt; : > $log
for pf in "$@"; do
  if [[ $pf == FIX:* ]]; then
    for d in $A $M; do $P -I $E/tools/apply_fixes_r3.py $d/ufs-weather-model ${pf#FIX:} >/dev/null || { echo "ABORT: $pf on $d" | tee -a $log; exit 1; }; done
    echo "applied $pf (apply_fixes_r3.py)" | tee -a $log
    continue
  fi
  pf=$(readlink -f "$pf")
  ok=""; base=""
  for b in . UFSATM UFSATM/fv3/atmos_cubed_sphere UFSATM/fv3 UFSATM/ccpp UFSATM/ccpp/physics UFSATM/ccpp/physics/physics; do
    for lev in 1 0 2; do
      if (cd $A/ufs-weather-model/$b && patch -p$lev --dry-run -F0 -s < "$pf" >/dev/null 2>&1); then ok=$lev; base=$b; break 2; fi
    done
  done
  [ -z "$ok" ] && { echo "ABORT: $pf does not apply cleanly to $A" | tee -a $log; exit 1; }
  (cd $A/ufs-weather-model/$base && patch -p$ok -F0 -s < "$pf")
  if ! (cd $M/ufs-weather-model/$base && patch -p$ok -F0 -s --dry-run < "$pf" >/dev/null 2>&1); then
    echo "ABORT: $pf applies to the plain tree but not the metered twin (meter context clash)" | tee -a $log; exit 1
  fi
  (cd $M/ufs-weather-model/$base && patch -p$ok -F0 -s < "$pf")
  echo "applied -p$ok in $base: $(basename $pf) md5 $(md5sum < $pf | cut -c1-12)" | tee -a $log
done
cd $E
[ -n "${NOBUILD:-}" ] && { echo "trees ready (NOBUILD)" | tee -a $log; exit 0; }
sbatch -J e_all_$tag --export=NONE,SRC=$A/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_mall_$tag --export=NONE,SRC=$M/ufs-weather-model,CLEAN=YES build64.sbatch
