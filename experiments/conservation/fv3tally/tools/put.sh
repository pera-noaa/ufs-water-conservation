#!/bin/bash
# put.sh <local file> <remote path under $U/cons/fv3tally> : upload via broker (gzip+base64, 30 kB chunks)
set -euo pipefail
F=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/fv3tally
b=$(gzip -9c "$1" | base64 | tr -d '\n')
n=${#b}; c=30000; i=0
broker run --timeout 60 hercules -- "mkdir -p \$(dirname $F/$2) && : > $F/$2.b64"
while [ $i -lt $n ]; do
  broker run --timeout 60 hercules -- "printf %s '${b:$i:$c}' >> $F/$2.b64"
  i=$((i+c))
done
broker run --timeout 60 hercules -- "base64 -d $F/$2.b64 | gunzip > $F/$2 && rm -f $F/$2.b64 && md5sum $F/$2 | cut -c1-12"
