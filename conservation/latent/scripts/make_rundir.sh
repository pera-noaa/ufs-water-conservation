#!/bin/bash
# Make a 24 h C96 control_p8_ugwpv1 run dir with six passive tracers from the wb_m19_di720 template (read-only),
# as trsamf/bin/make_rundir.sh, in $W/rt. Env options: OUTFH (output_fh list), RSTI (restart_interval), LAYOUT (e.g. 4,6),
# FSCAV (fscav_aero value, default "*:0.0"), SUITE (ccpp_suite), ICD (IC dir).
# usage: make_rundir.sh <name> <fv3.exe> [VAR=VAL ... exported at run time via env.sh]
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; T=$U/cons/tracer; W=$U/cons/latent
name=${1:?name}; exe=${2:?exe}; shift 2; icd=${ICD:-$T/ic}
src=$U/rt/wb_m19_di720; dst=$W/rt/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude='atmf*' --exclude='sfcf*' --exclude='PET*' --exclude=ESMF_Profile.summary --exclude=err \
  --exclude=out --exclude=job_timestamp.txt --exclude='log.atm.f*' --exclude='logfile.*' --exclude='warnfile.*' \
  --exclude='RESTART/*' --exclude='GFS*.Grb*' --exclude='*.nc_nccmp.log' --exclude=INPUT --exclude=budget_by_scheme.txt \
  --exclude=fv3.exe "$src/" "$dst/"
cd "$dst"
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
for t in pt_dyn_nopbl pt_cnv pt_plume pt_umoist pt_ghg pt_udry; do
  printf '"gfs_dyn",     "%s",  "%s",  "fv3_history",    "all",  .false.,  "none",  2\n' $t $t >> diag_table
done
fs=${FSCAV:-*:0.0}
sed -i -E "s/^(\s*fscav_aero\s*=\s*).*/\1\"$fs\"/" input.nml
[ -n "${LAYOUT:-}" ] && sed -i -E "s/^(\s*layout\s*=\s*).*/\1$LAYOUT/" input.nml
[ -n "${SUITE:-}" ] && sed -i -E "s/^(\s*ccpp_suite\s*=\s*).*/\1'$SUITE'/" input.nml
[ -n "${OUTFH:-}" ] && sed -i -E "s/^(output_fh:\s+).*/\1$OUTFH/" model_configure
[ -n "${RSTI:-}" ] && sed -i -E "s/^(restart_interval:\s+).*/\1$RSTI/" model_configure
cp "$exe" fv3.exe
: > env.sh
for kv in "$@"; do echo "export $kv" >> env.sh; done
echo "$name: $(grep -E '^\s*(fscav_aero|layout|ccpp_suite)\s*=' input.nml | tr -s ' ' | tr '\n' ' ') $(grep -E '^(output_fh|restart_interval):' model_configure | tr -s ' ' | tr '\n' ' ') env: $(tr '\n' ' ' < env.sh) exe: $(md5sum < fv3.exe | cut -c1-8)"
