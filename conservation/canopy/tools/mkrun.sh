#!/bin/bash
# usage: mkrun.sh <name> <exe> [input.nml sed expr] [model_configure sed expr] [env K=V ...]
# copies runs/tmpl (24 h control_p8_ugwpv1 C96, dt 720; real field_table), sets the exe, submits; prints job id
set -euo pipefail
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy
name=${1:?name}; exe=${2:?exe}; sedx=${3:-}; mcx=${4:-}; shift 4 2>/dev/null || shift $#
dst=$C/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude=fv3.exe.ctl64 --exclude=budget_by_scheme.txt $C/runs/tmpl/ $dst/
[ -L $dst/field_table ] && { echo "ABORT: field_table is a link"; exit 1; }
cp "$exe" $dst/fv3.exe
cd $dst
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"cr_$name\"/" job_card
[ -n "${JOBMIN:-}" ] && sed -i -E "s/^#SBATCH --time=.*/#SBATCH --time=$JOBMIN/" job_card
[ -n "$sedx" ] && sed -i -E "$sedx" input.nml
[ -n "$mcx" ] && sed -i -E "$mcx" model_configure
for kv in "$@"; do sed -i "s/^srun /export $kv\nsrun /" job_card; grep -q "^export $kv$" job_card || { echo "ABORT env"; exit 1; }; done
sbatch job_card | awk '{print $NF}'
