#!/bin/bash
# usage: put.sh <local file>... ; copies via broker stdin into $L/bin (real files)
L=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent
for f in "$@"; do broker run --timeout 60 hercules -- "cat > $L/bin/$(basename $f) && wc -c < $L/bin/$(basename $f)" < "$f"; done
