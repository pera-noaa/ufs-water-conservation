#!/bin/bash
# Turn a kept UFS regression-test run directory into a 24 h water-budget run for water_budget_by_scheme.py:
# native cubed-sphere output every 6 h, 3-D tendency diagnostics on, the dtend_* fields added to diag_table.
# usage: make_wb_rundir.sh <rt run dir> <new run dir> <job name> <diag_table holding the dtend_* lines> [fv3.exe]
set -euo pipefail
src=${1:?rt run dir}; dst=${2:?new run dir}; name=${3:?job name}; dref=${4:?reference diag_table}; exe=${5:-}
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude='atmf*' --exclude='sfcf*' --exclude='PET*' --exclude=ESMF_Profile.summary --exclude=err \
  --exclude=out --exclude=job_timestamp.txt --exclude='log.atm.f*' --exclude='logfile.*' --exclude='warnfile.*' \
  --exclude='RESTART/*' --exclude='GFS*.Grb*' --exclude='*.nc_nccmp.log' "$src/" "$dst/"
cd "$dst"
sed -i -E 's/^(restart_interval:\s+).*/\124/; s/^(write_dopost:\s+).*/\1.false./; s/^(output_grid:\s+).*/\1cubed_sphere_grid/; s/^(output_fh:\s+).*/\10 6 12 18 24/' model_configure
sed -i -E 's/^(\s*ldiag3d\s*=\s*).*/\1.true./; s/^(\s*qdiag3d\s*=\s*).*/\1.true./' input.nml
grep -q '"dtend_qv_pbl"' diag_table || grep '"dtend_' "$dref" >> diag_table
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"$name\"/" job_card
[ -n "$exe" ] && cp "$exe" fv3.exe
for k in restart_interval write_dopost output_grid output_fh; do grep -E "^$k:" model_configure; done
grep -E '^\s*(ldiag3d|qdiag3d|fhzero)\s*=' input.nml
echo "dtend lines: $(grep -c '"dtend_' diag_table); job: $(grep -- '--job-name' job_card)"
