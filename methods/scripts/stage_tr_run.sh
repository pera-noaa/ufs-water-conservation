#!/bin/bash
# Stage and submit a passive-tracer meter run (trpa profile, trpb 3-D IC) from the wbfzdnefk run directory.
# Usage: bash stage_tr_run.sh <TAG> <EXE> [HOURS=24] [QOS=batch] [MINUTES=30] [FH_STEP=6]  ->  rt/wb_herc_tr_<TAG>
# INPUT becomes a real directory of links to the original files, except gfs_data.tile*.nc, which are copies with trpb
# added (make_tr_ic.py); field_table and diag_table get trpa/trpb (edit_tr_tables.py). Nothing outside the new run
# directory is written. NOTR=1 stages the same run without the tracers (unmodified tables and IC) as a control.
set -e
TAG=${1:?TAG}; E=${2:?EXE}; HOURS=${3:-24}; QOS=${4:-batch}; MIN=${5:-30}; FHS=${6:-6}
R=/work2/noaa/co2/ash/ufs-chem-v1/rt
W=/work2/noaa/co2/ash/ufs-chem-v1/variants/wbtr
PY=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
B=$R/wb_herc_wbfzdnefk
[ -x "$E" ] || { echo "missing $E"; exit 1; }
D=$R/wb_herc_tr_$TAG
[ -e "$D" ] && { echo "exists: $D (pick a new TAG)"; exit 1; }
mkdir -p "$D/RESTART" "$D/modulefiles" "$D/INPUT"
cd "$B"
for e in *; do
  case "$e" in INPUT|RESTART|fv3.exe|modulefiles|atmf*|sfcf*|err|out|PET*|ESMF_Profile*|job_timestamp.txt|budget_by_scheme.txt|failed_try1|logfile*|warnfile*|log.atm.*|*.log) ;;
    *) cp -P "$e" "$D/$e";; esac
done
SI=$(readlink -f "$B/INPUT")
[ -d "$D/INPUT" ] || { echo "no $D/INPUT"; exit 1; }
for f in "$SI"/*; do
  n=$(basename "$f")
  case "$n" in gfs_data.tile*.nc) ;; *) ln -s "$f" "$D/INPUT/$n";; esac
done
if [ "${NOTR:-0}" = 1 ]; then
  for t in 1 2 3 4 5 6; do ln -s "$SI/gfs_data.tile$t.nc" "$D/INPUT/gfs_data.tile$t.nc"; done
else
  "$PY" -I "$W/scripts/make_tr_ic.py" "$SI" "$D/INPUT"
  "$PY" -I "$W/scripts/edit_tr_tables.py" "$D"
fi
ln -s "$E" "$D/fv3.exe"
cp "$B/modulefiles/"* "$D/modulefiles/"
fh=$(seq 0 "$FHS" "$HOURS" | paste -sd' ')
sed -i -e "s/^nhours_fcst:.*/nhours_fcst:             $HOURS/" -e "s/^restart_interval:.*/restart_interval:        $HOURS/" \
       -e "s/^output_fh:.*/output_fh:               $fh/" "$D/model_configure"
sed -i -e "s/^#SBATCH --qos=.*/#SBATCH --qos=$QOS/" -e "s/^#SBATCH --time=.*/#SBATCH --time=$MIN/" \
       -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"wb_tr_$TAG\"/" "$D/job_card"
grep -q "nhours_fcst: *$HOURS$" "$D/model_configure" && grep -q -- "--qos=$QOS" "$D/job_card" || { echo "staging edit failed"; exit 1; }
NT=2; [ "${NOTR:-0}" = 1 ] && NT=0
[ "$(grep -c '"trp[ab]"' "$D/field_table")" = $NT ] && [ "$(grep -c '"trp[ab]"' "$D/diag_table")" = $NT ] || { echo "table edit failed"; exit 1; }
echo "tr_$TAG: $(cd "$D" && sbatch job_card)"
