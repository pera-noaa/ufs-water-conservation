#!/bin/bash
# runs1.sh : fix gates and tallies (<= 2 own jobs at a time). nohup bash runs1.sh > ../logs/runs1.log 2>&1 &
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; F=$U/cons/fv3tally
ON=$E/runs/final9_switches.sed
X() { echo "s/^(\s*consv_te\s*=.*)$/\1\n  dyn_te_exact = $1/"; }
mine=""
slot() { while :; do n=0; for j in ${mine//,/ }; do squeue -h -j $j 2>/dev/null | grep -q . && n=$((n+1)); done; [ $n -lt 2 ] && return; sleep 30; done; }
sub() { slot; j=$("$@" | awk '/Submitted batch job/{print $4} /^S=/{print}'); echo "$(date +%T) $2 -> $j"; mine="$mine,$(echo $j | grep -o '[0-9]\{8\}' | tr '\n' ',')"; }
cd $F
sub tools/mkrun.sh fx_off    $F/exe/fv3_t_fx.exe  0
sub tools/mkrun.sh mfx_off   $F/exe/fv3_t_mfx.exe 1
sub tools/mkrun.sh mfx_d31   $F/exe/fv3_t_mfx.exe 1 ""  "$(X 31)"
sub tools/mkrun.sh mfx_d127  $F/exe/fv3_t_mfx.exe 1 ""  "$(X 127)"
sub tools/mkrun.sh mfx_on31  $F/exe/fv3_t_mfx.exe 1 $ON "$(X 31)"
sub tools/mkrun.sh mfx_on127 $F/exe/fv3_t_mfx.exe 1 $ON "$(X 127)"
sub tools/mkrun.sh fx_d31    $F/exe/fv3_t_fx.exe  0 ""  "$(X 31)"
sub tools/mkrun.sh fx_c999   $F/exe/fv3_t_fx.exe  0 ""  "s/^(\s*consv_te\s*=\s*).*/\10.999/"
sub tools/mkrestart.sh rs  $F/exe/fv3_t_fx.exe ""   "$(X 127)" $ON
sub tools/mkrestart.sh rsL $F/exe/fv3_t_fx.exe "4,6" "$(X 127)" $ON
slot; echo "$(date +%T) ALL SUBMITTED"
