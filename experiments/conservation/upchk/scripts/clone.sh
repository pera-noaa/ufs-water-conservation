#!/bin/bash
# usage: clone.sh <dir> <url> <sha> : clone a WM PR head with its pinned submodules, record SHAs
set -euo pipefail
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/upchk
d=$C/${1:?dir}; url=${2:?url}; sha=${3:?sha}
[ -e "$d" ] && { echo "ABORT: $d exists"; exit 1; }
mkdir -p $d && cd $d
git clone -q "$url" ufs-weather-model
cd ufs-weather-model
git checkout -q "$sha"
git submodule update --init --recursive -q
echo "WM $(git rev-parse HEAD)"
git submodule status --recursive | awk '{print $2, $1}' | grep -E '^(UFSATM|UFSATM/ccpp/physics|UFSATM/fv3/atmos_cubed_sphere|UFSATM/ccpp/framework) '
echo CLONE_DONE
