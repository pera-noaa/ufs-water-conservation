#!/bin/bash
# usage: mkfake.sh <dir> : fake ufs-weather-model tree from fxsrc (physics files under UFSATM/ccpp/physics/physics, data under UFSATM/ccpp/data)
set -e
L=/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2
d=${1:?dir}; rm -rf "${d:?}"; mkdir -p "$d/UFSATM/ccpp/physics/physics" "$d/UFSATM/ccpp/data"
for x in CONV Interstitials SFC_Layer SFC_Models Radiation; do cp -R "$L/fxsrc/$x" "$d/UFSATM/ccpp/physics/physics/"; done
cp -R "$L/fxsrc/data/." "$d/UFSATM/ccpp/data/"
