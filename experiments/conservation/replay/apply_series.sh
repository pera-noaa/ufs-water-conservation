#!/bin/bash
# usage: apply_series.sh <ufs-weather-model tree> [label-to-skip ...]
# Applies patches/series.txt in order, each with patch -F0 (no fuzz) in its recorded directory and -p level.
# Base: develop @112b1d46 + water diffs 01-19 + 09b (= $U/p20rt_final/ufs-weather-model = $U/cons/energy/base).
# Reproduces $U/cons/energy/full14. 56_NOFMA is the -no-fma build setting used for the bitwise gates (not proposed):
# `apply_series.sh <tree> 56_NOFMA` gives the proposed series alone. Row 16 is retired (merged into 43); the full13
# series is in patches_full13/ (apply it with `PATCHES=patches_full13 apply_series.sh <tree>`).
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd)/${PATCHES:-patches}
T=$(cd "${1:?tree}" && pwd); shift; skip=" $* "; only=" ${ONLY:-} "   # ONLY="NN_label ..." applies just those
n=0
while IFS=$'\t' read -r f dir lev _; do
  [[ "$skip" == *" ${f%.diff} "* ]] && { echo "skipped $f"; continue; }
  [ -n "${ONLY:-}" ] && [[ "$only" != *" ${f%.diff} "* ]] && continue
  (cd "$T/$dir" && patch -p"$lev" -F0 --no-backup-if-mismatch -s < "$D/$f") || { echo "FAILED at $f"; exit 1; }
  n=$((n+1))
done < "$D/series.txt"
left=$(find "$T" \( -name '*.rej' -o -name '*.orig' \) -newer "$D/series.txt" | head -3)
[ -z "$left" ] || { echo "FAILED: left behind $left"; exit 1; }
echo "applied $n diffs at -F0"
