#!/bin/bash
# fi_stage.sh <name> <exe> <consv_te> : forecast-impact run dir from the RT control_p8_intel run (mlm on, gaussian output); sbatch it
set -euo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm; S=$R/rt/stmp/apera/FV3_RT/rt_3564876/control_p8_intel
name=$1; exe=$2; cte=$3; D=$R/runs/$name
[ -e $D ] && { echo "ABORT: $D exists"; exit 1; }
mkdir -p $D/RESTART
cd $S
for e in *; do
  case "$e" in atmf*|sfcf*|GFS*|RESTART|out|err|PET*|logfile*|log.atm*|ESMF_Profile*|job_timestamp.txt|warnfile*|*.log|input.nml|model_configure|diag_table|job_card|fv3.exe|modulefiles|ufs.configure|*.nc.*) ;;
    *) ln -s "$S/$e" "$D/$e";; esac
done
cp $S/input.nml $S/model_configure $S/diag_table $S/job_card $S/ufs.configure $D/; cp -r $S/modulefiles $D/
cd $D; cp $exe fv3.exe
grep -q '^  mlm          = .true.' input.nml || { echo "ABORT: no mlm"; exit 1; }
sed -i "s/^  consv_te = .*/  consv_te = $cte/" input.nml; grep -q "^  consv_te = $cte\$" input.nml || { echo "ABORT: consv_te"; exit 1; }
sed -i -e "/^#SBATCH/ s/--job-name=[^ ]*/--job-name=fi_$name/" -e "/^#SBATCH -J/ s/-J [^ ]*/-J fi_$name/" job_card
grep -q "$S" job_card && { echo "ABORT: job_card references the template"; exit 1; }
echo "$name exe=$(md5sum < fv3.exe | cut -c1-8) consv_te=$cte $(sbatch --parsable job_card)"
