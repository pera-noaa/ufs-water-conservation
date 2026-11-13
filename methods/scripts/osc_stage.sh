#!/bin/bash
# Stage and submit a no-tracer C96 run into rt/wb_herc_osc<TAG> (cold start from wbfzdnefk's INPUT, or warm start from a restart set).
# Usage: bash osc_stage.sh <TAG> <EXE> <HOURS> "<OUTPUT_FH>" [MINUTES=60]
# Environment: RST="<hours>" restart times (default: none before HOURS); WARM=<run dir>:<fhrot> warm start from
#   <run dir>/RESTART/<prefix>.* at hour fhrot; OSCENV="K=V K2=V2" exported before srun; NMLSET="key=val" (input.nml),
#   MCSET="key:val" (model_configure) overrides. Writes only the new run dir.
set -e
TAG=${1:?TAG}; E=${2:?EXE}; HOURS=${3:?HOURS}; OFH=${4:?OUTPUT_FH}; MIN=${5:-60}
R=/work2/noaa/co2/ash/ufs-chem-v1/rt
B=$R/wb_herc_wbfzdnefk
[ -x "$E" ] || { echo "missing $E"; exit 1; }
D=$R/wb_herc_osc$TAG
[ -e "$D" ] && { echo "exists: $D (pick a new TAG)"; exit 1; }
mkdir -p "$D/RESTART" "$D/modulefiles" "$D/INPUT"
cd "$B"
for e in *; do
  case "$e" in INPUT|RESTART|fv3.exe|modulefiles|atmf*|sfcf*|err|out|PET*|ESMF_Profile*|job_timestamp.txt|budget_by_scheme.txt|failed_try1|logfile*|warnfile*|log.atm.*|*.log) ;;
    *) cp -P "$e" "$D/$e";; esac
done
SI=$(readlink -f "$B/INPUT")
ln -s "$E" "$D/fv3.exe"
cp "$B/modulefiles/"* "$D/modulefiles/"
sed -i -e "s/^nhours_fcst:.*/nhours_fcst:             $HOURS/" -e "s/^restart_interval:.*/restart_interval:        ${RST:-$HOURS}/" \
       -e "s/^output_fh:.*/output_fh:               $OFH/" "$D/model_configure"
if [ -n "${WARM:-}" ]; then
  WD=${WARM%%:*}; FH=${WARM##*:}
  PFX=$(date -u -d "2021-03-22 06:00 UTC + $FH hours" +%Y%m%d.%H0000)
  ls "$WD/RESTART/$PFX.coupler.res" >/dev/null
  for f in "$SI"/*; do case "$(basename "$f")" in gfs_ctrl.nc|gfs_data.*|sfc_data.*) ;; *) ln -s "$f" "$D/INPUT/$(basename "$f")";; esac; done
  for f in "$WD/RESTART/$PFX".*; do ln -s "$f" "$D/INPUT/${f##*/$PFX.}"; done
  sed -i -e "s/^fhrot:.*/fhrot:                   $FH/" "$D/model_configure"
  sed -i -e "s/^ *warm_start *=.*/  warm_start = .true./" -e "s/^ *external_ic *=.*/  external_ic = .false./" \
         -e "s/^ *nggps_ic *=.*/  nggps_ic = .false./" -e "s/^ *make_nh *=.*/  make_nh = .false./" \
         -e "s/^ *mountain *=.*/  mountain = .true./" -e "s/^ *na_init *=.*/  na_init = 0/" \
         -e "s/^ *nstf_name *=.*/  nstf_name    = 2,0,0,0,0/" "$D/input.nml"
  grep -q "warm_start = .true." "$D/input.nml" && grep -q "na_init = 0" "$D/input.nml" && grep -q "fhrot: *$FH$" "$D/model_configure" \
    || { echo "warm edit failed"; exit 1; }
else
  for f in "$SI"/*; do ln -s "$f" "$D/INPUT/$(basename "$f")"; done
fi
for kv in ${NMLSET:-}; do
  k=${kv%%=*}; v=${kv#*=}
  [ "$(grep -c "^ *$k *=" "$D/input.nml")" = 1 ] || { echo "namelist key $k not unique"; exit 1; }
  sed -i "s/^ *$k *=.*/  $k = $v/" "$D/input.nml"
done
for kv in ${MCSET:-}; do
  k=${kv%%:*}; v=${kv#*:}
  [ "$(grep -c "^$k:" "$D/model_configure")" = 1 ] || { echo "model_configure key $k not unique"; exit 1; }
  sed -i "s/^$k:.*/$k:                $v/" "$D/model_configure"
done
sed -i -e "s/^#SBATCH --qos=.*/#SBATCH --qos=batch/" -e "s/^#SBATCH --time=.*/#SBATCH --time=$MIN/" \
       -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"wb_osc$TAG\"/" "$D/job_card"
grep -q "nhours_fcst: *$HOURS$" "$D/model_configure" && grep -q -- "--qos=batch" "$D/job_card" || { echo "staging edit failed"; exit 1; }
[ "$(grep -c '"trp[ab]"' "$D/field_table")" = 0 ] || { echo "tracer tables in base"; exit 1; }
for kv in ${OSCENV:-}; do
  sed -i "s/^srun /export $kv\nsrun /" "$D/job_card"
  grep -q "^export $kv$" "$D/job_card" || { echo "env edit failed"; exit 1; }
done
echo "osc$TAG: $(cd "$D" && sbatch job_card)"
