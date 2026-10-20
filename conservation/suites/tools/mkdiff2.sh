#!/bin/bash
# mkdiff2.sh <out.diff> <base dir> <relpath>... : diff <base>/<relpath> vs work/<relpath> (series diffs that apply in order)
cd "$(dirname "$0")/.."
out=$1; base=$2; shift 2; : > "$out"
for r in "$@"; do diff -u --label "a/UFSATM/ccpp/$r" --label "b/UFSATM/ccpp/$r" "$base/$r" "work/$r" >> "$out"; done
echo "$out: $(grep -c '^[-+][^-+]' "$out") changed lines"
