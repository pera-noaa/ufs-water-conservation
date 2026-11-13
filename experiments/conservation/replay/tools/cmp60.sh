#!/bin/bash
# usage: cmp60.sh <treeA> <treeB> : compare the files of logs/changed_files.txt (every file base -> full13 changes);
# prints the differing ones with their changed-line counts
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay; n=0
while read -r f; do
  cmp -s "$1/$f" "$2/$f" || { n=$((n+1)); echo "  differs: $f ($(diff "$1/$f" "$2/$f" | grep -c '^[<>]') lines)"; }
done < ${CHANGED:-$R/logs/changed_files.txt}
echo "files differing: $n"
