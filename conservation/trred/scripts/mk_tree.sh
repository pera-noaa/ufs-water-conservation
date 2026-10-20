#!/bin/bash
# usage: mk_tree.sh <name> <src tree> [x.py ...] ; rsync copy (no .git/builds/exes) into $W/<name>, then run x.py <tree>
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trred; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
t=${1:?name}; SB=${2:?src}; shift 2
[ -e "$W/$t" ] && { echo "ABORT $W/$t exists"; exit 1; }
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$SB/" "$W/$t/"
for f in "$@"; do $P -I "$f" "$W/$t"; done
echo "TREE_OK $W/$t"
