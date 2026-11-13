#!/bin/bash
# usage: analyze1.sh > logs/analysis1.txt ; impact tables for list1 (24 h runs), noise = p0 vs p0c
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $C/runs
K="GLOBAL|evcw_ave|trans_ave|sbsno_ave|LAND  lhtfl|tmp2m|spfh2m|cnwat|OCEAN lhtfl|OCEAN shtfl|tmp_hyblev1"
imp() { [ -e "$1/sfcf024.tile6.nc" ] && [ -e "$2/sfcf024.tile6.nc" ] || { echo "== $3: missing"; return; }
  echo "== $3 ($2 - $1)"; $P -I ../tools/impact.py $1 $2 6 24 | grep -E "$K"; }
imp p0 p0c "NOISE consv_te 0.999"
for p in "p0 q0 gate-off" "q0 qF1 E2-opt1" "q0 qALL all-mine"; do set -- $p
  [ -e "$2/sfcf024.tile6.nc" ] && echo "BITCMP $3 $1 $2: $($P -I ../tools/bitcmp.py $1 $2 24 | tail -1)"; done
imp q0 qF1 "E2 opt1 mass-weighted"
imp q0 qF2 "E2 opt2 larger"
imp q0 qF3 "E2 opt3 dominant phase (v5)"
imp qT8 q0 "TH8 effect, E2 off (TH9 off)"
imp qT8F1 qF1 "TH8 effect, E2 opt1 (TH9 off)"
imp qT8 qT9 "TH8+TH9 effect, E2 off"
imp qT8F1 qT9F1 "TH8+TH9 effect, E2 opt1"
imp q0 qT9 "TH9 effect given TH8, E2 off"
imp qF1 qT9F1 "TH9 effect given TH8, E2 opt1"
imp q0 qS1 "E1 spray implicit"
imp q0 qALL "all three on (E2 opt1, TH9, E1)"
for r in q0 qS1 qALL; do [ -e $r/out ] && $P -I ../tools/spr.py $r/out --cells 3; done
