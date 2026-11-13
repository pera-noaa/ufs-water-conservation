#!/bin/bash
# usage: hput.sh <local file> <remote file> ; chunked gzip+base64 over `broker run hercules` (remote must be in canopy)
set -euo pipefail
l=${1:?local}; r=${2:?remote}
case "$r" in /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy/*) ;; *) echo "refuse: outside canopy"; exit 1;; esac
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy/xfer
tmp=$(mktemp); gzip -c "$l" | base64 > "$tmp"
broker run --timeout 60 hercules -- "mkdir -p $T; : > $T/put.b64" >/dev/null
split -b 60000 "$tmp" "$tmp.part."
for p in "$tmp".part.*; do
  broker run --timeout 120 hercules -- "cat >> $T/put.b64 <<'B64EOF'
$(cat "$p")
B64EOF" >/dev/null
done
rm -f "$tmp" "$tmp".part.*
lm5=$(md5 -q "$l")
rm5=$(broker run --timeout 60 hercules -- "base64 -d $T/put.b64 | gunzip -c > '$r.tmp' && mv '$r.tmp' '$r' && case '$r' in *.sh) chmod +x '$r';; esac && md5sum '$r'" | tail -1 | cut -d' ' -f1)
[ "$rm5" = "$lm5" ] && echo "OK $r" || { echo "MD5 MISMATCH $r"; exit 1; }
