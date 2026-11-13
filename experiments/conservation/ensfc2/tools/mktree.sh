#!/bin/bash
# usage: mktree.sh <name> <src: fx0|mfx0> <steps...> ; steps: nofma meters fixes bugfix options d3a
# builds $D/<name>/ufs-weather-model from a source tree (build dirs excluded), then applies the steps in order
set -euo pipefail
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
name=${1:?name}; src=${2:?src}; shift 2
dst=$D/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
mkdir -p "$dst"
rsync -a --exclude='tests/build_*' --exclude='tests/*.exe' --exclude='tests/log_*' "$D/$src/ufs-weather-model" "$dst/"
T=$dst/ufs-weather-model
for s in "$@"; do
  case $s in
    nofma)   $PY $D/tools/nofma.py $T ;;
    meters)  for m in instrument_es_sfc instrument_es_sfc2 es_static es_icefix instrument_es_sfc3 instrument_es_sfc4 instrument_es_sfc5; do $PY $D/tools/$m.py $T; done ;;
    fixes)   $PY $D/tools/apply_sfc_fixes.py $T SI1 SI2 NP1 ;;
    bugfix)  $PY $D/tools/apply_bugfix.py $T QR1 CMC FL1 ;;
    options) $PY $D/tools/apply_options.py $T ;;
    d3a)     (cd $T && patch -p1 --no-backup-if-mismatch < /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/patches/01_D3A.diff) ;;
    meters2) for m in instrument_es2_r3 instrument_es2_r3b instrument_es2_r3c instrument_es2_r3d; do $PY $D/tools/$m.py $T; done ;;
    meters4) $PY $D/tools/instrument_es2_r4.py $T ;;
    nm12)    (cd $T/UFSATM/ccpp/physics && patch -p1 --no-backup-if-mismatch < $D/patches/20_NM12_noahmp_combine_melt_out.diff) ;;
    bugfix4) $PY $D/tools/apply_bugfix_r4.py $T SL2 CS1 CB1 ;;
    metersx) for m in instrument_es2_r4b instrument_es2_r4c instrument_es2_r4d; do $PY $D/tools/$m.py $T; done ;;
    options4) $PY $D/tools/apply_options_r4.py $T ;;
    *) echo "unknown step $s"; exit 1 ;;
  esac
done
echo "TREE_DONE $name"
