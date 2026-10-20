#!/bin/bash
# usage: mk_repo_diffs.sh <base tree> <final tree> : one combined diff per repository (base -> final), paths relative to
# the submodule root (-p1). Checks each applies at -F0 to a scratch copy of the base submodule and reproduces final.
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay
B=${1:?base}; F=${2:?final}; O=$R/repo_diffs; rm -rf "${O:?}"; mkdir -p $O
for spec in "fv3atm_GFDL_atmos_cubed_sphere:UFSATM/fv3/atmos_cubed_sphere" "ccpp-physics:UFSATM/ccpp/physics" \
            "UFSATM:UFSATM" "noahmp:NOAHMP-interface/noahmp" "ufs-weather-model_build_setting:."; do
  name=${spec%%:*}; root=${spec#*:}; out=$O/$name.diff; : > $out
  while read -r f; do
    case $name in
      UFSATM) [[ $f == UFSATM/* && $f != UFSATM/fv3/atmos_cubed_sphere/* && $f != UFSATM/ccpp/physics/* ]] || continue ;;
      ufs-weather-model_build_setting) [[ $f != UFSATM/* && $f != NOAHMP-interface/* ]] || continue ;;
      *) [[ $f == $root/* ]] || continue ;;
    esac
    rel=${f#$root/}; [ "$root" = . ] && rel=$f
    diff -u --label "a/$rel" --label "b/$rel" "$B/$f" "$F/$f" >> $out
  done < $R/logs/changed_files.txt
  S=$R/scratch_repo; rm -rf "${S:?}"; mkdir -p $S
  grep "^+++ b/" $out | sed 's#^+++ b/##' | while read -r rel; do mkdir -p $S/$(dirname $rel); cp "$B/$root/$rel" $S/$rel; done
  (cd $S && patch -p1 -F0 -s --no-backup-if-mismatch < $out) || echo "ABORT $name: does not apply"
  bad=0; for rel in $(grep "^+++ b/" $out | sed 's#^+++ b/##'); do cmp -s $S/$rel "$F/$root/$rel" || bad=$((bad+1)); done
  printf "%-34s files %3d  +%-5d -%-5d  applies -p1 -F0 on base/%s, reproduces final: %s\n" $name \
    $(grep -c "^+++ " $out) $(grep -c "^+[^+]" $out) $(grep -c "^-[^-]" $out) $root $([ $bad = 0 ] && echo yes || echo "NO ($bad)")
  rm -rf "${S:?}"
done
