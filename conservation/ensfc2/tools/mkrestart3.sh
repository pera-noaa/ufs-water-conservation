#!/bin/bash
# usage: mkrestart3.sh <name> <fv3 exe> ["nml opts"] ; <name>_S = 24 h with a 12 h restart, <name>_R = warm start at 12 h (afterok)
set -euo pipefail
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2
name=${1:?name}; exe=${2:?exe}; opts=${3:-}
S=$D/runs/${name}_S; R=$D/runs/${name}_R
for d in $S $R; do [ -e "$d" ] && { echo "ABORT: $d exists"; exit 1; }; done
for d in $S $R; do
  rsync -a --exclude=fv3.exe.ctl64 $D/runs/tmpl/ $d/
  cp "$exe" $d/fv3.exe
  sed -i -E 's/^(restart_interval:\s+).*/\112 -1/' $d/model_configure
  if [ -n "$opts" ]; then
    ins=$(echo "$opts" | tr ';' '\n' | sed 's/^/  /' | sed ':a;N;$!ba;s/\n/\\n/g')
    sed -i -E "0,/^(\s*iopt_trs\s*=.*)$/s//\1\n$ins/" $d/input.nml
  fi
done
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"${name}_S\"/" $S/job_card
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"${name}_R\"/" $R/job_card
sed -i -E 's/^(fhrot:\s+).*/\112/' $R/model_configure
sed -i -E 's/^(\s*warm_start\s*=\s*).*/\1.true./; s/^(\s*nggps_ic\s*=\s*).*/\1.false./; s/^(\s*external_ic\s*=\s*).*/\1.false./; s/^(\s*make_nh\s*=\s*).*/\1.false./; s/^(\s*mountain\s*=\s*).*/\1.true./; s/^(\s*na_init\s*=\s*).*/\10/; s/^(\s*nstf_name\s*=\s*).*/\12,0,0,0,0/' $R/input.nml
src=$(readlink -f $D/runs/tmpl/INPUT)
rm -f $R/INPUT; mkdir $R/INPUT
cp -L $src/grid_spec.nc $src/*_mosaic.nc $src/*_grid.tile*.nc $src/oro_data*.nc $R/INPUT/
cat > $R/stage_restart.sh <<STG
#!/bin/bash
set -euo pipefail
for f in $S/RESTART/20210322.180000.*; do cp "\$f" INPUT/"\$(basename "\$f" | sed 's/^20210322\.180000\.//')"; done
ls INPUT | grep -c res
STG
sed -i "0,/^set -eux/s//set -eux\nbash .\/stage_restart.sh/" $R/job_card
cd $S; js=$(sbatch --parsable job_card)
cd $R; jr=$(sbatch --parsable --dependency=afterok:$js job_card)
echo "S=$js R=$jr"
