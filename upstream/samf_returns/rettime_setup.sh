#!/bin/bash
# rettime_setup.sh (login node): the WM develop tree for rettime_build.sb
set -eu
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; R=$P/rettime/wm; WM_BASE=783f524a
[ -e $R ] || rsync -a --exclude '/tests/*.exe' --exclude '/tests/logs/log_*/' --exclude '/build_*/' "$P/rt2/" "$R/"
cd $R
git checkout -q -- tests/logs/ tests/test_changes.list
git fetch -q origin develop
[ "$(git rev-parse --short=8 FETCH_HEAD)" = "$WM_BASE" ] || { echo "GATE: WM develop moved"; exit 1; }
git checkout -q -B rettime $WM_BASE
git submodule sync -q --recursive
git submodule update -q --init --recursive 2>/dev/null || true
echo SETUP_DONE $(git rev-parse --short=8 HEAD)
