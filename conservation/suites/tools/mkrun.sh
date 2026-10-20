#!/bin/bash
# mkrun.sh <name> <exe tag> <test> [key=value ...] : $S/runs/<name> from $S/tmpl/<test>; key=value edits input.nml
#   (e.g. consv_te=0.999); INPUT holds symlinks to the template's own INPUT files (read only)
set -euo pipefail
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
name=${1:?name}; exe=${2:?exe}; t=${3:?test}; shift 3
src=$S/tmpl/$t; dst=$S/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
[ -e "$S/exe/$exe.exe" ] || { echo "ABORT: no exe $exe"; exit 1; }
mkdir -p $dst/INPUT $dst/RESTART
rsync -a --exclude=INPUT --exclude='RESTART/*' "$src/" "$dst/"
for f in $src/INPUT/*; do ln -s "$f" "$dst/INPUT/$(basename $f)"; done
cp -p $S/exe/$exe.exe $dst/fv3.exe
cd $dst
for kv in "$@"; do
  k=${kv%%=*}; v=${kv#*=}
  if [[ $k == mc:* ]]; then k=${k#mc:}
    grep -qE "^$k:" model_configure || { echo "ABORT: $k not in model_configure"; exit 1; }
    sed -i -E "s/^($k:\s+).*/\1$v/" model_configure; echo "  $name: $(grep -E "^$k:" model_configure)"; continue
  fi
  if [[ $k == gfs:* ]]; then k=${k#gfs:}
    grep -qE "^\s*$k\s*=" input.nml && { echo "ABORT: $k already set"; exit 1; }
    sed -i -E "s/^(\s*&gfs_physics_nml\s*)$/\1\n  $k = $v/" input.nml
    grep -qE "^\s*$k\s*=" input.nml || { echo "ABORT: $k not added"; exit 1; }
  elif grep -qE "^\s*$k\s*=" input.nml; then sed -i -E "s/^(\s*$k\s*=\s*).*/\1$v/" input.nml
  else echo "ABORT: $k not in input.nml"; exit 1; fi
  echo "  $name: $(grep -E "^\s*$k\s*=" input.nml | tr -s ' ')"
done
echo "$exe $t $*" > run_info
