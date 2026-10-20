#!/bin/bash
# usage: gocart_prep.sh <run name> : add chemistry tracer pt_udry after no3an3 (field_table), fscav 0 for it,
# diag output, IC copies with pt_udry = 1e-6 (float64) in $W/ic_g (made once)
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
cd $W/rtn/${1:?}
awk 'BEGIN{d=0} {print} /"no3an3"/{f=1} f && /profile_type/ && !d {print " \"TRACER\", \"atmos_mod\", \"pt_udry\"\n           \"longname\",     \"uniform dry test tracer\"\n           \"units\",        \"kg/kg\"\n       \"tracer_usage\", \"chemistry\"\n       \"profile_type\", \"fixed\", \"surface_value=0.0\" /"; d=1}' field_table > ft && mv ft field_table
sed -i -E 's/^(\s*fscav_aero\s*=\s*.*)$/\1,"pt_udry:0.0"/' input.nml
printf '"gfs_dyn",     "pt_udry",  "pt_udry",  "fv3_history",    "all",  .false.,  "none",  2\n' >> diag_table
if [ ! -e $W/ic_g/done ]; then mkdir -p $W/ic_g; $P -I $W/bin/add_tracer_ic.py INPUT $W/ic_g pt_udry > $W/ic_g/log; touch $W/ic_g/done; fi
for f in $W/ic_g/gfs_data*.nc; do rm -f INPUT/$(basename $f); ln -s $f INPUT/$(basename $f); done
grep -n 'pt_udry' field_table | head -2; grep -c '"TRACER"' field_table; grep -o 'pt_udry:0.0' input.nml
