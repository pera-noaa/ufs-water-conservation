#!/bin/bash
# usage: mkrestart.sh <name> <fv3 exe> [layout, e.g. 4,6 or ""] [input.nml sed -E expression] ; restart test: <name>_S = 24 h straight with a 12 h restart,
# <name>_R = warm start from <name>_S/RESTART at 12 h to 24 h (submitted afterok). Compare *f024 and RESTART at 24 h.
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy
name=${1:?name}; exe=${2:?exe}; lay=${3:-}; nmlsed=${4:-}
S=$E/runs/${name}_S; R=$E/runs/${name}_R
for d in $S $R; do [ -e "$d" ] && { echo "ABORT: $d exists"; exit 1; }; done
for d in $S $R; do
  rsync -a --exclude=fv3.exe.ctl64 --exclude=budget_by_scheme.txt $E/runs/tmpl/ $d/
  cp "$exe" $d/fv3.exe
  sed -i -E 's/^(restart_interval:\s+).*/\112 -1/' $d/model_configure
  [ -n "$lay" ] && sed -i -E "s/^(\s*layout\s*=\s*).*/\1$lay/" $d/input.nml
  [ -n "$nmlsed" ] && sed -i -E "$nmlsed" $d/input.nml
done
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"cr_${name}_S\"/" $S/job_card
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"cr_${name}_R\"/" $R/job_card
# warm start settings (tests/tests/control_restart_p8)
sed -i -E 's/^(fhrot:\s+).*/\112/' $R/model_configure
sed -i -E 's/^(\s*warm_start\s*=\s*).*/\1.true./; s/^(\s*nggps_ic\s*=\s*).*/\1.false./; s/^(\s*external_ic\s*=\s*).*/\1.false./; s/^(\s*make_nh\s*=\s*).*/\1.false./; s/^(\s*mountain\s*=\s*).*/\1.true./; s/^(\s*na_init\s*=\s*).*/\10/; s/^(\s*nstf_name\s*=\s*).*/\12,0,0,0,0/' $R/input.nml
# R: real INPUT dir; restart files staged inside the job, after S has finished
src=$(readlink -f $E/runs/tmpl/INPUT)
rm -f $R/INPUT; mkdir $R/INPUT
cp -L $src/grid_spec.nc $src/*_mosaic.nc $src/*_grid.tile*.nc $src/oro_data*.nc $R/INPUT/
cat > $R/stage_restart.sh <<STG
#!/bin/bash
# copy <name>_S restart files at 12 h into INPUT without their date prefix
set -euo pipefail
for f in $S/RESTART/20210322.180000.*; do cp "\$f" INPUT/"\$(basename "\$f" | sed 's/^20210322\.180000\.//')"; done
ls INPUT | grep -c res
STG
sed -i "0,/^set -eux/s//set -eux\nbash .\/stage_restart.sh/" $R/job_card
cd $S; js=$(sbatch --parsable job_card)
cd $R; jr=$(sbatch --parsable --dependency=afterok:$js job_card)
echo "S=$js R=$jr"
grep -E "^(fhrot|restart_interval)" $R/model_configure | tr '\n' ' '; grep -E "^\s*(warm_start|external_ic|nggps_ic|make_nh|mountain|na_init|layout|nstf_name)\s*=" $R/input.nml | tr -s ' ' | tr '\n' ' '; echo
