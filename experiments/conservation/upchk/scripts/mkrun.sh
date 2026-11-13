#!/bin/bash
# usage: mkrun.sh <name> <fv3 exe> [input.nml sed expr] [field_table] : copy the energy 24 h control_p8 template (read only),
# set exe, job name, account lpdm; optional namelist edit and field_table; submit. Prints the job id.
set -euo pipefail
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/upchk; T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy/runs/tmpl
name=${1:?name}; exe=${2:?exe}; sedx=${3:-}; ft=${4:-}
dst=$C/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
mkdir -p $C/runs
rsync -a --exclude=fv3.exe.ctl64 --exclude=out --exclude=err --exclude='*.nc' --exclude=RESTART --exclude=budget_by_scheme.txt $T/ $dst/
mkdir -p $dst/RESTART
# the template's history *.nc are outputs; INPUT and fixed fields are symlinks (kept by rsync -a as links)
for f in $T/*.nc; do [ -L "$f" ] && cp -P "$f" $dst/; done
cp "$exe" $dst/fv3.exe
cd $dst
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"uc_$name\"/; s/^#SBATCH --account=.*/#SBATCH --account=lpdm/" job_card
[ -n "$sedx" ] && sed -i -E "$sedx" input.nml
[ -n "$ft" ] && cp "$ft" field_table
echo "exe=$exe" > upchk_run.txt; echo "sed=$sedx" >> upchk_run.txt; echo "field_table=${ft:-template}" >> upchk_run.txt
sbatch --parsable job_card
