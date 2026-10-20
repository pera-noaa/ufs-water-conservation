#!/bin/bash
# mkrs.sh <name> <exe tag> <test> [key=value ...] : restart + decomposition red team (after energy/meters/tools/mkrestart.sh)
#   <name>_S 24 h straight with a 12 h restart; <name>_R warm start 12->24 h from _S/RESTART; <name>_L 24 h layout 4,6
#   one job: S and L concurrently, then R. Compare *f024 and RESTART of S vs R, S vs L.
set -euo pipefail
S0=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
name=${1:?}; exe=${2:?}; t=${3:?}; shift 3
for x in S R L; do bash $S0/tools/mkrun.sh ${name}_$x $exe $t "$@" >/dev/null; done
S=$S0/runs/${name}_S; R=$S0/runs/${name}_R; L=$S0/runs/${name}_L
for d in $S $R; do sed -i -E 's/^(restart_interval:\s+).*/\112 -1/' $d/model_configure; done
sed -i -E "s/^(\s*layout\s*=\s*).*/\14,6/" $L/input.nml
sed -i -E 's/^(fhrot:\s+).*/\112/' $R/model_configure
sed -i -E 's/^(\s*warm_start\s*=\s*).*/\1.true./; s/^(\s*nggps_ic\s*=\s*).*/\1.false./; s/^(\s*external_ic\s*=\s*).*/\1.false./; s/^(\s*make_nh\s*=\s*).*/\1.false./; s/^(\s*mountain\s*=\s*).*/\1.true./; s/^(\s*na_init\s*=\s*).*/\10/; s/^(\s*nstf_name\s*=\s*).*/\12,0,0,0,0/' $R/input.nml
# R: real files for the restart, staged inside the job after S
rm -f $R/INPUT/gfs_data* $R/INPUT/gfs_ctrl.nc $R/INPUT/sfc_data*
grep -E "^(fhrot|restart_interval)" $R/model_configure | tr '\n' ' '; grep -E "^\s*(warm_start|external_ic|nggps_ic|make_nh|mountain|na_init|nstf_name)\s*=" $R/input.nml | tr -s ' ' | tr '\n' ' '; echo
grep -E "^\s*layout" $L/input.nml
