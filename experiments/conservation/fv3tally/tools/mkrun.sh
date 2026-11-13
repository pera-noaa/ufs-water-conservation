#!/bin/bash
# usage: mkrun.sh <name> <fv3 exe> <tally 0|1> [sed file for input.nml] [extra sed expr]
# copy energy's 24 h control_p8_ugwpv1 template into my runs dir, set exe/job name/FV3_ETALLY, submit
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; F=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/fv3tally
name=${1:?name}; exe=${2:?exe}; tal=${3:?tally}; sedf=${4:-}; sedx=${5:-}
dst=$F/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude=fv3.exe.ctl64 --exclude=fv3.exe $E/runs/tmpl/ $dst/
cp "$exe" $dst/fv3.exe
cd $dst
for f in input.nml job_card model_configure; do [ -L $f ] && { cp --remove-destination "$(readlink -f $f)" $f; }; done
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"$name\"/" job_card
sed -i -E "s/^#SBATCH --time=.*/#SBATCH --time=40/" job_card
sed -i -E "s/^(export OMP_NUM_THREADS=1)$/\1\nexport FV3_ETALLY=$tal/" job_card
grep -q "^export FV3_ETALLY=$tal" job_card || { echo "ABORT: FV3_ETALLY not set"; exit 1; }
[ -n "$sedf" ] && sed -i -E -f "$sedf" input.nml
[ -n "$sedx" ] && sed -i -E "$sedx" input.nml
[ -n "${MCSED:-}" ] && sed -i -E "$MCSED" model_configure
sbatch job_card
