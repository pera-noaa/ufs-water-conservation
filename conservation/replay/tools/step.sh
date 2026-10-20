#!/bin/bash
# usage: step.sh <tree> <NN_label> <method> <args...> : apply one series step to <tree> (a ufs-weather-model root),
# log it, and write the step's regenerated diff (pre -> post over every file it touched, -p1 paths at the tree root).
#   P  <dir> <lev> <diff>              plain: patch -p<lev> -F0 in <tree>/<dir>; must apply without a reject
#   PR <dir> <lev> <diff> <tool...>    patch -F0, keep rejects, then run <tool...> (TREE in it = <tree>); no .rej may remain
#   S  <tool...>                       script step (anchors), no diff
#   M  <F> <dir:lev:diff>...           compose/rebase: apply each diff in turn with patch -F<F> (fuzz allowed), no
#                                      reject may remain; the step's diff is the regenerated pre -> post
#   X  <from> <to> <rel...>            extract: patch <tree> with diff -u <from>/<rel> <to>/<rel> (integrator stage trees)
# Out: $R/work/regen/<NN_label>.diff, one line appended to $R/logs/replay.tsv:
#   NN_label method result(clean|offset|rebased|script|extracted) source md5 hunks offsets rejects
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay
T=${1:?tree}; NL=${2:?NN_label}; M=${3:?method}; shift 3
W=$R/work${WTAG:-}; mkdir -p $W/regen $W/pre $W/plog
LIST=$W/pre/list.txt; cp ${CHANGED:-$R/logs/changed_files.txt} $LIST
src=""; dir=.; lev=1
case $M in P|PR) dir=$1; lev=$2; src=$3; shift 3
  lsdiff --strip=$lev "$src" | sed "s#^#$dir/#; s#^\./##" >> $LIST ;;
  X) xf=$1; xt=$2; shift 2; for r in "$@"; do echo "$r" >> $LIST; done ;;
  M) fz=$1; shift; for s3 in "$@"; do IFS=: read -r d3 l3 f3 <<< "$s3"; lsdiff --strip=$l3 "$f3" | sed "s#^#$d3/#; s#^\./##" >> $LIST; done ;;
esac
sort -u $LIST -o $LIST
rm -rf "${W:?}/pre/t"; mkdir -p $W/pre/t
while read -r f; do [ -e "$T/$f" ] && { mkdir -p "$W/pre/t/$(dirname "$f")"; cp -p "$T/$f" "$W/pre/t/$f"; }; done < $LIST
res=""; hunks=0; offs=0; rejs=0; log=$W/plog/$NL.txt; : > $log
case $M in
  P|PR)
    (cd "$T/$dir" && patch -p$lev -F0 --no-backup-if-mismatch < "$src") > $log 2>&1; rc=$?
    offs=$(grep -c "(offset" $log); rejs=$(grep -c "FAILED" $log)
    if [ $M = P ]; then
      [ $rc -eq 0 ] && [ $rejs -eq 0 ] || { echo "ABORT $NL: does not apply at -F0"; grep -E "FAILED|malformed|can't" $log | head; exit 1; }
      [ $offs -gt 0 ] && res=offset || res=clean
    else
      tool=("${@//TREE/$T}"); "${tool[@]}" >> $log 2>&1 || { echo "ABORT $NL: tool failed"; tail -3 $log; exit 1; }
      [ $rejs -gt 0 ] && res=rebased || res=clean
    fi ;;
  M) : > $log; rc=0
     for s3 in "$@"; do IFS=: read -r d3 l3 f3 <<< "$s3"; echo "== $f3" >> $log
       (cd "$T/$d3" && patch -p$l3 -F$fz --no-backup-if-mismatch < "$f3") >> $log 2>&1 || rc=1; done
     [ $rc -eq 0 ] || { echo "ABORT $NL: compose failed"; grep -E "FAILED" $log | head; exit 1; }
     offs=$(grep -c "(offset" $log); rejs=$(grep -c "with fuzz" $log); src="$*"; res=composed ;;
  S) tool=("${@//TREE/$T}"); "${tool[@]}" > $log 2>&1 || { echo "ABORT $NL: script failed"; tail -3 $log; exit 1; }; res=script ;;
  X) for r in "$@"; do diff -u --label "a/$r" --label "b/$r" "$xf/$r" "$xt/$r"; done > $W/pre/x.diff
     (cd "$T" && patch -p1 -F0 --no-backup-if-mismatch < $W/pre/x.diff) > $log 2>&1 || { echo "ABORT $NL: extract does not apply"; tail -3 $log; exit 1; }
     src=$W/pre/x.diff; res=extracted ;;
  *) echo "method?"; exit 1 ;;
esac
left=$(find "$T" -name "*.rej" -o -name "*.orig" | head -5)
[ -z "$left" ] || { echo "ABORT $NL: left behind: $left"; exit 1; }
out=$W/regen/$NL.diff; : > $out
while read -r f; do
  a="$W/pre/t/$f"; [ -e "$a" ] || a=/dev/null; b="$T/$f"; [ -e "$b" ] || b=/dev/null
  diff -u --label "a/$f" --label "b/$f" "$a" "$b" >> $out
done < $LIST
nf=$(grep -c "^+++ " $out)
md=-; [ -n "$src" ] && [ -f "$src" ] && { md=$(md5sum < "$src" | cut -c1-12); hunks=$(grep -c "^@@" "$src"); }
printf "%s\t%s\t%s\t%s\t%s\thunks=%s\toffsets=%s\trejects=%s\tfiles=%s\n" "$NL" "$M" "$res" "${src:-script}" "$md" "$hunks" "$offs" "$rejs" "$nf" >> $R/logs/replay${WTAG:-}.tsv
echo "$NL $M $res files=$nf offsets=$offs rejects=$rejs"
