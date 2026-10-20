#!/bin/bash
# usage: put.sh <local file> [remote dir]  ; copies via broker stdin into $T/bin (default)
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer
f=${1:?file}; d=${2:-$T/bin}
broker run --timeout 60 hercules -- "mkdir -p $d && cat > $d/$(basename $f) && wc -c $d/$(basename $f)" < "$f"
