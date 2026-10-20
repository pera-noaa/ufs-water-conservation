#!/bin/bash
# Make a 24 h C96 control_p8_ugwpv1 run dir with six passive tracers from the wb_m19_di720 template (read-only).
# usage: make_rundir.sh <name> <fv3.exe> [walltime_min] [IC dir with gfs_data.tile*.nc]
# trunif: adds shadow tracers sh_d sh_m sh_p sh_v (chemistry type) after the six test tracers, plus env TAGS (e.g.
# TAGS='tg_adv tg_rmp tg_pbl tg_dcv tg_scv'); job name prefix tu_
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; T=$U/cons/tracer; W=$U/cons/trunif; W=$U/cons/trunif
name=${1:?name}; exe=${2:?exe}; wt=${3:-40}; icd=${4:-$T/ic}
src=$U/rt/wb_m19_di720; dst=$W/rt/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
mkdir -p "$W/rt"
rsync -a --exclude='atmf*' --exclude='sfcf*' --exclude='PET*' --exclude=ESMF_Profile.summary --exclude=err \
  --exclude=out --exclude=job_timestamp.txt --exclude='log.atm.f*' --exclude='logfile.*' --exclude='warnfile.*' \
  --exclude='RESTART/*' --exclude='GFS*.Grb*' --exclude='*.nc_nccmp.log' --exclude=INPUT --exclude=budget_by_scheme.txt \
  --exclude=fv3.exe "$src/" "$dst/"
cd "$dst"
# never write through template symlinks (they point into the shared RT dir)
for f in field_table diag_table input.nml model_configure job_card ufs.configure; do
  if [ -L "$f" ]; then cp --remove-destination "$(readlink -f "$f")" "$f"; fi
  [ -L "$f" ] && { echo "ABORT: $f still a symlink"; exit 1; }
done
mkdir INPUT
srcin=$(readlink -f "$src/INPUT")
for f in "$srcin"/*; do b=$(basename "$f"); case $b in gfs_data.tile*) ln -s "$icd/$b" "INPUT/$b";; *) ln -s "$f" "INPUT/$b";; esac; done
cat >> field_table <<'FT'
# passive test tracers (tracer-mass conservation study)
 "TRACER", "atmos_mod", "pt_dyn_nopbl"
           "longname",     "structured passive tracer with physics changes discarded (nopbl)"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_cnv"
           "longname",     "structured generic passive tracer (SAMF transport)"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_plume"
           "longname",     "plume passive tracer zero over most of the globe"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_umoist"
           "longname",     "uniform moist mixing ratio"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_ghg"
           "longname",     "structured chemistry-type passive tracer (SAMF chem path and PBL)"
           "units",        "kg/kg"
       "tracer_usage", "chemistry"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_udry"
           "longname",     "uniform dry mixing ratio chemistry type"
           "units",        "kg/kg"
       "tracer_usage", "chemistry"
       "profile_type", "fixed", "surface_value=0.0" /
FT
for t in sh_d sh_m sh_p sh_v ${TAGS:-}; do
  printf ' "TRACER", "atmos_mod", "%s"\n           "longname",     "shadow tracer (reset each process)"\n           "units",        "kg/kg"\n       "tracer_usage", "chemistry"\n       "profile_type", "fixed", "surface_value=0.0" /\n' $t >> field_table
done
for t in pt_dyn_nopbl pt_cnv pt_plume pt_umoist pt_ghg pt_udry; do
  printf '"gfs_dyn",     "%s",  "%s",  "fv3_history",    "all",  .false.,  "none",  2\n' $t $t >> diag_table
done
sed -i -E 's/^(\s*fscav_aero\s*=\s*).*/\1"*:0.0"/' input.nml
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"tu_$name\"/; s/^#SBATCH --time=.*/#SBATCH --time=$wt/" job_card
cp "$exe" fv3.exe
grep -E '^\s*fscav_aero' input.nml; grep -c pt_ diag_table; grep -c '"TRACER"' field_table
grep -E -- '--job-name|--time' job_card; ls -la INPUT | grep gfs_data | head -2
