#!/bin/bash
# runs3.sh : v2 regate (<= 2 own jobs)
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; F=$U/cons/fv3tally
ON=$E/runs/final9_switches.sed
X() { echo "s/^(\s*consv_te\s*=.*)$/\1\n  dyn_te_exact = $1/"; }
mine=""
slot() { while :; do n=0; for j in ${mine//,/ }; do squeue -h -j $j 2>/dev/null | grep -q . && n=$((n+1)); done; [ $n -lt 2 ] && return; sleep 30; done; }
sub() { slot; j=$("$@" | awk '/Submitted batch job/{print $4} /^S=/{print}'); echo "$(date +%T) $2 -> $j"; mine="$mine,$(echo $j | grep -o '[0-9]\{8\}' | tr '\n' ',')"; }
cd $F
while pgrep -f "bash mkfx2.sh" > /dev/null; do sleep 30; done
for t in fx2 mfx2; do cp -p $F/$t/ufs-weather-model/tests/fv3_t_$t.exe $F/exe/ || { echo "ABORT: no $t exe"; exit 1; }; done
for j in $(squeue -h -u apera -o "%i %j" | awk '$2 ~ /^t_(hyd2|mg2|fx2|mfx2)$/{print $1}'); do mine="$mine,$j"; done
sub tools/mkrun.sh fx2_off    $F/exe/fv3_t_fx2.exe  0
sub tools/mkrun.sh mfx2_d31   $F/exe/fv3_t_mfx2.exe 1 ""  "$(X 31)"
sub tools/mkrun.sh mfx2_on31  $F/exe/fv3_t_mfx2.exe 1 $ON "$(X 31)"
sub tools/mkrun.sh mfx2_d127  $F/exe/fv3_t_mfx2.exe 1 ""  "$(X 127)"
sub tools/mkrun.sh fx2_d31    $F/exe/fv3_t_fx2.exe  0 ""  "$(X 31)"
sub tools/mkrestart.sh rs2  $F/exe/fv3_t_fx2.exe ""   "$(X 127)" $ON
sub tools/mkrestart.sh rsL2 $F/exe/fv3_t_fx2.exe "4,6" "$(X 127)" $ON
slot; echo "$(date +%T) ALL SUBMITTED"
