#!/bin/bash
# Stage and submit a gc* run of an executable (copy of rt/stage_dev_run_long.sh, own tree): gc_stage_run.sh <TAG> <EXE> [HOURS=50] [QOS=batch]
set -e
TAG=${1:?TAG}; E=${2:?EXE}; HOURS=${3:-50}; QOS=${4:-batch}
case "$TAG" in gc*) ;; *) echo "TAG must start with gc"; exit 1;; esac
R=/work2/noaa/co2/ash/ufs-chem-v1/rt
B=$R/wb_herc_wbfzdnefk
[ -x "$E" ] || { echo "missing $E"; exit 1; }
D=$R/wbgc_$TAG
[ -e "$D" ] && { echo "exists: $D (pick a new TAG)"; exit 1; }
mkdir -p "$D/RESTART" "$D/modulefiles"
cd "$B"
for e in *; do
  case "$e" in RESTART|fv3.exe|modulefiles|atmf*|sfcf*|err|out|PET*|ESMF_Profile*|job_timestamp.txt|budget_by_scheme.txt|failed_try1|logfile*|warnfile*|log.atm.*|*.log) ;;
    *) cp -P "$e" "$D/$e";; esac
done
ln -s "$E" "$D/fv3.exe"
cp "$B/modulefiles/"* "$D/modulefiles/"
fh=$(seq 0 ${OUTH:-24} "$HOURS" | paste -sd" ")
sed -i -e "s/^nhours_fcst:.*/nhours_fcst:             $HOURS/" -e "s/^restart_interval:.*/restart_interval:        $HOURS/" \
       -e "s/^output_fh:.*/output_fh:               $fh/" "$D/model_configure"
sed -i -e "s/^#SBATCH --qos=.*/#SBATCH --qos=$QOS/" -e "s/^#SBATCH --time=.*/#SBATCH --time=${WALL:-40}/" \
       -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"wbgc_$TAG\"/" "$D/job_card"
grep -q "nhours_fcst: *$HOURS$" "$D/model_configure" && grep -q -- "--qos=$QOS" "$D/job_card" || { echo "staging edit failed"; exit 1; }
echo "$TAG: $D $(cd "$D" && sbatch job_card)"
