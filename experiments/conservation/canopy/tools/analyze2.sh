#!/bin/bash
# usage: analyze1.sh > logs/analysis1.txt ; impact tables for list1 (24 h runs), noise = p0 vs p0c
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $C/runs
K="GLOBAL|evcw_ave|trans_ave|sbsno_ave|LAND  lhtfl|tmp2m|spfh2m|cnwat|OCEAN lhtfl|OCEAN shtfl|tmp_hyblev1"
imp() { [ -e "$1/sfcf024.tile6.nc" ] && [ -e "$2/sfcf024.tile6.nc" ] || { echo "== $3: missing"; return; }
  echo "== $3 ($2 - $1)"; $P -I ../tools/impact.py $1 $2 6 24 | grep -E "$K"; }
imp qF1 qF1c "NOISE with E2 opt1 (consv_te 0.999)"
imp qF2 qF2c "NOISE with E2 opt2 (consv_te 0.999)"
imp qT8 qT8F1 "E2 opt1 own impact, TH8 off"
imp qT8 qT8F2 "E2 opt2 own impact, TH8 off"
imp qT9 qT9F1 "E2 opt1 impact, TH8+TH9 on"
imp qT9 qT9F2 "E2 opt2 impact, TH8+TH9 on"
imp qT8F2 qF2 "TH8 effect, E2 opt2 (TH9 off)"
imp qT8F2 qT9F2 "TH8+TH9 effect, E2 opt2"
imp qF2 qT9F2 "TH9 effect given TH8, E2 opt2"
