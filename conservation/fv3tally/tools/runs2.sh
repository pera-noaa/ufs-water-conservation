#!/bin/bash
# runs2.sh : sensitivity of the adiabatic remainder (mt exe, tally on, all switches off). <= 2 own jobs.
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; F=$U/cons/fv3tally
mine=""
slot() { while :; do n=0; for j in ${mine//,/ }; do squeue -h -j $j 2>/dev/null | grep -q . && n=$((n+1)); done; [ $n -lt 2 ] && return; sleep 30; done; }
sub() { slot; j=$("$@" | awk '/Submitted batch job/{print $4}'); echo "$(date +%T) $2 -> $j"; mine="$mine,$j"; }
cd $F
# wait for runs1.sh to finish submitting (its jobs count against the same 2-job budget)
while pgrep -f "bash runs1.sh" > /dev/null; do sleep 30; done
for j in $(squeue -h -u apera -o "%i %j" | awk '$2 ~ /^(fx_|mfx_|rs_|rsL_|rs|rsL)/{print $1}'); do mine="$mine,$j"; done
sub tools/mkrun.sh s_tr5  $F/exe/fv3_t_mt.exe 1 "" "s/^(\s*hord_tr\s*=\s*).*/\15/"
sub tools/mkrun.sh s_ns8  $F/exe/fv3_t_mt.exe 1 "" "s/^(\s*n_split\s*=\s*).*/\18/"
sub tools/mkrun.sh s_ks4  $F/exe/fv3_t_mt.exe 1 "" "s/^(\s*k_split\s*=\s*).*/\14/; s/^(\s*n_split\s*=\s*).*/\12/"
MCSED="s/^(dt_atmos:\s+).*/\1360/" sub tools/mkrun.sh s_dt360 $F/exe/fv3_t_mt.exe 1
slot; echo "$(date +%T) ALL SUBMITTED"
