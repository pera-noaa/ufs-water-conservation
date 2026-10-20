#!/bin/bash
# usage: mkrun_e.sh <name> <fv3 exe> [tend_opt_pbl tend_opt_gwd] [input.nml sed expr]
# copy of the energy 24 h control_p8_ugwpv1 template (read-only) into $L/rt/<name>; no submit (use mpar.sbatch)
set -euo pipefail
L=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent; E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
name=${1:?name}; exe=${2:?exe}; pbl=${3:-}; gwd=${4:-}; sedx=${5:-}
dst=$L/rt/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude=fv3.exe.ctl64 --exclude='RESTART/*' --exclude=budget_by_scheme.txt $E/runs/tmpl/ $dst/
cd $dst
for f in input.nml model_configure diag_table field_table job_card; do
  [ -L "$f" ] && cp --remove-destination "$(readlink -f "$f")" "$f"
  [ -L "$f" ] && { echo "ABORT: $f symlink"; exit 1; }
done
cp "$exe" fv3.exe
if [ -n "$pbl" ]; then
  [ "$(grep -c '^&gfs_physics_nml' input.nml)" = 1 ] || { echo "ABORT nml"; exit 1; }
  sed -i "/^&gfs_physics_nml/a\  tend_opt_pbl = $pbl\n  tend_opt_gwd = $gwd" input.nml
fi
[ -n "$sedx" ] && sed -i -E "$sedx" input.nml
: > env.sh
echo "$name: $(grep -E '^\s*(tend_opt_pbl|tend_opt_gwd|consv_te)\s*=' input.nml | tr -s ' ' | tr '\n' ' ') exe $(md5sum < fv3.exe | cut -c1-8)"
