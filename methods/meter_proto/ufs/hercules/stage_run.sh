#!/bin/bash
# usage: stage_run.sh <name> <exe> <modules.lua> <budget_meter T|F> <budget_hook T|F> [layout "IxJ"] [threads]
# run dir $M/runs/<name> from the kept rt_plain control_p8 run; native-grid output every 6 h; then sbatch
set -e
M=/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto
name=$1; exe=$2; mods=$3; bm=$4; bh=$5; lay=${6:-}; thr=${7:-}
S=$(ls -d $M/rt_plain/stmp/*/FV3_RT/rt_*/control_p8_intel | tail -1)
[ -d "$S" ] || { echo "no template"; exit 1; }
D=$M/runs/$name
[ -e $D ] && { echo "ABORT: $D exists"; exit 1; }
mkdir -p $D/RESTART $D/modulefiles
cd $S
for e in *; do
  case "$e" in atmf*|sfcf*|GFS*|RESTART|out|err|PET*|logfile*|log.atm*|ESMF_Profile*|job_timestamp.txt|warnfile*|*.log|input.nml|model_configure|diag_table|job_card|fv3.exe|modulefiles|ufs.configure|*.nc.*|mediator*) ;;
    *) ln -s "$S/$e" "$D/$e";; esac
done
cp $S/input.nml $S/model_configure $S/diag_table $S/job_card $D/
[ -f $S/ufs.configure ] && cp $S/ufs.configure $D/
cd $D
sed -i -e 's|^output_grid: .*|output_grid:             cubed_sphere_grid|' -e 's|^write_dopost: .*|write_dopost:            .false.|' \
       -e 's|^output_fh: .*|output_fh:               0 6 12 18 24|' -e 's|^restart_interval: .*|restart_interval:        24|' -e 's|^zstandard_level: .*|zstandard_level:         0|' model_configure
printf '\n&budget_nml\n  budget_meter = .%s.\n  budget_hook = .%s.\n/\n' $( [ $bm = T ] && echo true || echo false ) $( [ $bh = T ] && echo true || echo false ) >> input.nml
if [ -n "$lay" ]; then sed -i "s/^ *layout *= *.*/  layout = ${lay/x/,}/" input.nml; fi
if [ -n "$thr" ]; then I=$(grep -m1 "^ *layout" input.nml | sed "s/.*= *//; s/,.*//"); J=$(grep -m1 "^ *layout" input.nml | sed "s/.*, *//"); W=$(awk '/^write_tasks_per_group/{print $2}' model_configure); sed -i -e "s/^ATM_omp_num_threads: .*/ATM_omp_num_threads:            $thr/" -e "s/^ATM_petlist_bounds: .*/ATM_petlist_bounds:             0 $(( (I*J*6 + W)*thr - 1 ))/" ufs.configure; grep -E "omp|petlist" ufs.configure | tr -s " " | tr "\n" " "; echo; fi
cp $exe fv3.exe
cp $mods modulefiles/modules.fv3.lua
cp $(dirname $mods)/../modulefiles/ufs_common.lua modulefiles/ 2>/dev/null || true
sed -i -e "/^#SBATCH/ s/--job-name=[^ ]*/--job-name=mp_$name/" -e "/^#SBATCH -J/ s/-J [^ ]*/-J mp_$name/" job_card
grep -q "$S" job_card && { echo "ABORT: job_card references the template dir"; exit 1; }
echo "$name: $(grep -A3 budget_nml input.nml | tr -s ' ' | tr '\n' ' ') layout=$(grep -m1 ' layout' input.nml)"
sbatch job_card
