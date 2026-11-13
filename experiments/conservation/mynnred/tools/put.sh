#!/bin/bash
# put.sh <local file>... : copy local files to $U/cons/mynnred/tools on Hercules (via broker stdin)
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/mynnred/tools
for f in "$@"; do
  b=$(basename "$f")
  gzip -c "$f" | base64 | broker run --timeout 60 hercules -- "mkdir -p $R && base64 -d | gunzip > $R/$b.tmp && mv $R/$b.tmp $R/$b && md5sum $R/$b | cut -c1-8"
  echo "  local $(md5 -q "$f" | cut -c1-8) $b"
done
