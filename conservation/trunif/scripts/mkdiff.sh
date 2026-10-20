#!/bin/bash
# Meter diff of the trunif tree (shadow + tags) on top of the tracer agent's instrumented base. usage: mkdiff.sh
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trunif; T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer
P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
rm -rf "${W:?}/ref"; mkdir -p "$W/ref"
cd "$T/base"
rsync -aR UFSATM/fv3/atmos_cubed_sphere/model/fv_dynamics.F90 UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90 \
  UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/ UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f \
  UFSATM/ccpp/data/CCPP_typedefs.F90 "$W/ref/"
$P -I $W/bin/testhook_chem_pbl.py $W/ref > /dev/null
$P -I $W/bin/instrument_tm.py $W/ref $W/bin/tm_meter.F90 > /dev/null
$P -I $W/bin/testhook_uniform_reset.py $W/ref > /dev/null
cd "$W"
out=$W/bin/05_shadow_tags_meter.diff; : > "$out"
for f in $(cd ref && find . -type f | sort); do
  if ! cmp -s "ref/$f" "sh/$f"; then
    echo "CHANGED $f"
    diff -u "ref/$f" "sh/$f" | sed -e "s#^--- ref/\./#--- a/#" -e "s#^+++ sh/\./#+++ b/#" >> "$out" || true
  fi
done
wc -l "$out"
