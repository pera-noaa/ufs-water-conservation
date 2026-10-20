#!/bin/bash
# mkdiff.sh <out.diff> <relpath>... : diff src/<relpath> (pristine full10) vs work/<relpath>, a/ b/ prefixes (ccpp-physics -p1)
cd "$(dirname "$0")/.."
out=$1; shift; : > "$out"
for r in "$@"; do diff -u --label "a/UFSATM/ccpp/$r" --label "b/UFSATM/ccpp/$r" "src/$r" "work/$r" >> "$out"; done
echo "$out: $(grep -c '^[-+][^-+]' "$out") changed lines"
