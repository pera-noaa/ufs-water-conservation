#!/bin/bash
# usage: put.sh <local file>... ; copies via broker stdin into $W/bin (real files)
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trsamf
for f in "$@"; do broker run --timeout 60 hercules -- "cat > $W/bin/$(basename $f) && wc -c $W/bin/$(basename $f)" < "$f"; done
