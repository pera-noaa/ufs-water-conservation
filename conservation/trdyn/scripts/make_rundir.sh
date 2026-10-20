#!/bin/bash
# trdyn: 24 h C96 control_p8_ugwpv1 run dir from the wb_m19_di720 template (read-only), as trred/make_rundir.sh, plus
# chemistry-type tracers pt_cplume (plume, positivity test) and shadows sh_d sh_m sh_p sh_v (trunif meter).
# Env: ICD (IC dir, default $W/ic_m), LAYOUT, OUTFH, RSTI, NML ("key=val ..." appended to &fv_core_nml).
# usage: make_rundir.sh <name> <fv3.exe> [VAR=VAL ... exported at run time via env.sh]
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trdyn
name=${1:?name}; exe=${2:?exe}; shift 2; icd=${ICD:-$W/ic_m}
src=$U/rt/wb_m19_di720; dst=$W/rt/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
mkdir -p $W/rt
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
 "TRACER", "atmos_mod", "pt_cplume"
           "longname",     "plume chemistry type (positivity)"
           "units",        "kg/kg"
       "tracer_usage", "chemistry"
       "profile_type", "fixed", "surface_value=0.0" /
FT
for t in sh_d sh_m sh_p sh_v; do
  printf ' "TRACER", "atmos_mod", "%s"\n           "longname",     "shadow tracer (reset each process)"\n           "units",        "kg/kg"\n       "tracer_usage", "chemistry"\n       "profile_type", "fixed", "surface_value=0.0" /\n' $t >> field_table
done
for t in pt_dyn_nopbl pt_cnv pt_plume pt_umoist pt_ghg pt_udry pt_cplume; do
  printf '"gfs_dyn",     "%s",  "%s",  "fv3_history",    "all",  .false.,  "none",  2\n' $t $t >> diag_table
done
fs=${FSCAV:-*:0.0}; sed -i -E "s/^(\s*fscav_aero\s*=\s*).*/\1\"$fs\"/" input.nml
[ -n "${LAYOUT:-}" ] && sed -i -E "s/^(\s*layout\s*=\s*).*/\1$LAYOUT/" input.nml
[ -n "${OUTFH:-}" ] && sed -i -E "s/^(output_fh:\s+).*/\1$OUTFH/" model_configure
[ -n "${RSTI:-}" ] && sed -i -E "s/^(restart_interval:\s+).*/\1$RSTI/" model_configure
for kv in ${NML:-}; do sed -i -E "0,/^&fv_core_nml/s//\&fv_core_nml\n  ${kv}/" input.nml; done
cp "$exe" fv3.exe
: > env.sh
for kv in "$@"; do echo "export $kv" >> env.sh; done
echo "$name: $(grep -E '^\s*(fscav_aero|layout|dry_tracer_adv|dry_tracer_ic)\s*=' input.nml | tr -s ' ' | tr '\n' ' ') $(grep -E '^(output_fh|restart_interval):' model_configure | tr -s ' ' | tr '\n' ' ') env: $(tr '\n' ' ' < env.sh) ic: $icd exe: $(md5sum < fv3.exe | cut -c1-8)"
