#!/bin/bash
# usage: mkrun3.sh <name> <fv3 exe> ["nml1=v1;nml2=v2" gfs_physics_nml options] [layout e.g. 4,6] ; 24 h C96 run, submitted
set -euo pipefail
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2
name=${1:?name}; exe=${2:?exe}; opts=${3:-}; lay=${4:-}
dst=$D/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude=fv3.exe.ctl64 $D/runs/tmpl/ $dst/
cp "$exe" $dst/fv3.exe
cd $dst
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"$name\"/" job_card
[ -n "$lay" ] && sed -i -E "s/^(\s*layout\s*=\s*).*/\1$lay/" input.nml
if [ -n "$opts" ]; then
  ins=$(echo "$opts" | tr ';' '\n' | sed 's/^/  /' | sed ':a;N;$!ba;s/\n/\\n/g')
  sed -i -E "0,/^(\s*iopt_trs\s*=.*)$/s//\1\n$ins/" input.nml
fi
grep -E "^\s*(layout|noahmp_|precip_phase|lw_sfc|sfc_evap)" input.nml | tr -s ' ' | tr '\n' ' '; echo
sbatch job_card
