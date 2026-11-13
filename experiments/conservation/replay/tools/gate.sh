#!/bin/bash
# usage: gate.sh <name> [label-to-skip ...] : fresh copy of the base, apply_series.sh (skipping the given labels),
# then diff -r against $E/${FINAL:-full13} (env FINAL) (excluding .git, build dirs, executables, compile logs/modules, *.orig/*.rej).
# PASS = no difference.
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay; E=$R/../energy
G=$R/gate/${1:?name}; shift
rm -rf "${G:?}"; mkdir -p $R/gate
rsync -a --exclude="tests/build_*" --exclude="*.exe" --exclude="tests/compile_*_time.log" --exclude="tests/modules.fv3_*" \
  $E/base/ufs-weather-model/ $G/
$R/apply_series.sh $G "$@" | tail -2
$R/tools/cmptree.sh $G $E/${FINAL:-full13}/ufs-weather-model $R/logs/gate_$(basename $G).txt
sed "s#$E/${FINAL:-full13}/ufs-weather-model#${FINAL:-full13}#g; s#$G#replay#g" $R/logs/gate_$(basename $G).txt | head -5
[ -s $R/logs/gate_$(basename $G).txt ] && echo "GATE $(basename $G): FAIL" || echo "GATE $(basename $G): PASS (diff -r empty)"
