#!/bin/bash
# usage: mk_warm.sh <R run> <S run> : turn $W/rt/<R> (made by make_rundir.sh) into a 12 h warm start from <S>/RESTART at
# 2021-03-22 18 UTC (settings as energy/mkrestart.sh = tests/control_restart_p8); restart files staged by pre.sh at run time.
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn
R=$W/rt/${1:?}; S=$W/rt/${2:?}
cd $R
sed -i -E 's/^(fhrot:\s+).*/\112/' model_configure
sed -i -E 's/^(\s*warm_start\s*=\s*).*/\1.true./; s/^(\s*nggps_ic\s*=\s*).*/\1.false./; s/^(\s*external_ic\s*=\s*).*/\1.false./; s/^(\s*make_nh\s*=\s*).*/\1.false./; s/^(\s*mountain\s*=\s*).*/\1.true./; s/^(\s*na_init\s*=\s*).*/\10/; s/^(\s*nstf_name\s*=\s*).*/\12,0,0,0,0/' input.nml
src=$(readlink -f INPUT/grid_spec.nc); src=$(dirname $src)
rm -rf INPUT; mkdir INPUT
cp -L $src/grid_spec.nc $src/*_mosaic.nc $src/*_grid.tile*.nc $src/oro_data*.nc INPUT/
cat > pre.sh <<STG
#!/bin/bash
set -euo pipefail
for f in $S/RESTART/20210322.180000.*; do cp "\$f" INPUT/"\$(basename "\$f" | sed 's/^20210322\.180000\.//')"; done
echo "staged \$(ls INPUT | grep -c res) restart files"
STG
grep -E "^(fhrot|restart_interval|output_fh)" model_configure | tr -s ' ' | tr '\n' ' '; grep -E "^\s*(warm_start|external_ic|nggps_ic|make_nh|mountain|na_init|nstf_name)\s*=" input.nml | tr -s ' ' | tr '\n' ' '; echo
