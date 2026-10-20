#!/bin/bash
# put.sh <local file>... : copy local files to $S/tools on Hercules (via broker stdin)
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/tools
for f in "$@"; do
  b=$(basename "$f")
  gzip -c "$f" | base64 | broker run --timeout 60 hercules -- "base64 -d | gunzip > $S/$b.tmp && mv $S/$b.tmp $S/$b && md5sum $S/$b | cut -c1-8"
  echo "  local $(md5 -q "$f" | cut -c1-8) $b"
done
