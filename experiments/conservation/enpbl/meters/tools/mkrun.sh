#!/bin/bash
# usage: mkrun.sh <name> <fv3 exe> [nml sed expr] ; copy the 24 h control_p8 template, set exe and job name, submit
set -euo pipefail
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/enpbl
name=${1:?name}; exe=${2:?exe}; sedx=${3:-}
dst=$D/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a $D/runs/tmpl/ $dst/
cp "$exe" $dst/fv3.exe
cd $dst
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"$name\"/" job_card
[ -n "$sedx" ] && sed -i -E "$sedx" input.nml
grep -n -E "dspheat|consv_te" input.nml
sbatch job_card
