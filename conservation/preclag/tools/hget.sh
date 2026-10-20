#!/bin/bash
# usage: hget.sh <remote file> <local file> ; chunked gzip+base64 over `broker run hercules`
set -euo pipefail
r=${1:?remote}; l=${2:?local}
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/preclag/xfer
n=$(broker run --timeout 120 hercules -- "mkdir -p $T; gzip -c '$r' | base64 -w0 > $T/get.b64; stat -c %s $T/get.b64" | tail -1)
CH=60000; : > "$l.b64"
off=0
while [ "$off" -lt "$n" ]; do
  broker run --timeout 120 hercules -- "tail -c +$((off+1)) $T/get.b64 | head -c $CH" >> "$l.b64"
  off=$((off+CH))
done
[ "$(wc -c < "$l.b64" | tr -d ' ')" = "$n" ] || { echo "size mismatch"; exit 1; }
base64 -d -i "$l.b64" | gunzip -c > "$l"; rm -f "$l.b64"
rm5=$(broker run --timeout 60 hercules -- "md5sum '$r'" | tail -1 | cut -d' ' -f1)
lm5=$(md5 -q "$l"); [ "$rm5" = "$lm5" ] && echo "OK $l $lm5" || { echo "MD5 MISMATCH $l"; exit 1; }
