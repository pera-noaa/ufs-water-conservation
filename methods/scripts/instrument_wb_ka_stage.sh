#!/bin/bash
# Stage and submit a no-tracer C96 run (as stage_tr_run.sh NOTR=1, from the wbfzdnefk run directory) into rt/wb_herc_ka<TAG>.
# Usage: bash instrument_wb_ka_stage.sh <TAG> <EXE> <HOURS> "<OUTPUT_FH list>" [MINUTES=60] [QOS=batch]
# KSW=<step> in the environment adds "export WKA_KSW=<step>" (instrument_wb_ka_switch.py builds: A before, A' from it).
# INPUT is a directory of links to the original files; nothing outside the new run directory is written.
set -e
TAG=${1:?TAG}; E=${2:?EXE}; HOURS=${3:?HOURS}; OFH=${4:?OUTPUT_FH}; MIN=${5:-60}; QOS=${6:-batch}
R=/work2/noaa/co2/ash/ufs-chem-v1/rt
B=$R/wb_herc_wbfzdnefk
[ -x "$E" ] || { echo "missing $E"; exit 1; }
D=$R/wb_herc_ka$TAG
[ -e "$D" ] && { echo "exists: $D (pick a new TAG)"; exit 1; }
mkdir -p "$D/RESTART" "$D/modulefiles" "$D/INPUT"
cd "$B"
for e in *; do
  case "$e" in INPUT|RESTART|fv3.exe|modulefiles|atmf*|sfcf*|err|out|PET*|ESMF_Profile*|job_timestamp.txt|budget_by_scheme.txt|failed_try1|logfile*|warnfile*|log.atm.*|*.log) ;;
    *) cp -P "$e" "$D/$e";; esac
done
SI=$(readlink -f "$B/INPUT")
for f in "$SI"/*; do ln -s "$f" "$D/INPUT/$(basename "$f")"; done
ln -s "$E" "$D/fv3.exe"
cp "$B/modulefiles/"* "$D/modulefiles/"
sed -i -e "s/^nhours_fcst:.*/nhours_fcst:             $HOURS/" -e "s/^restart_interval:.*/restart_interval:        $HOURS/" \
       -e "s/^output_fh:.*/output_fh:               $OFH/" "$D/model_configure"
sed -i -e "s/^#SBATCH --qos=.*/#SBATCH --qos=$QOS/" -e "s/^#SBATCH --time=.*/#SBATCH --time=$MIN/" \
       -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"wb_ka$TAG\"/" "$D/job_card"
grep -q "nhours_fcst: *$HOURS$" "$D/model_configure" && grep -q -- "--qos=$QOS" "$D/job_card" || { echo "staging edit failed"; exit 1; }
[ "$(grep -c '"trp[ab]"' "$D/field_table")" = 0 ] || { echo "tracer tables in base"; exit 1; }
if [ -n "${KSW:-}" ]; then
  sed -i "s/^srun /export WKA_KSW=$KSW\nsrun /" "$D/job_card"
  grep -q "^export WKA_KSW=$KSW$" "$D/job_card" || { echo "KSW edit failed"; exit 1; }
fi
echo "ka$TAG: $(cd "$D" && sbatch job_card)"
