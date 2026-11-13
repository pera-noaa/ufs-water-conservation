#!/bin/bash
# usage: stage.sh <name> <exe> <modules.lua> <budget_probe T|F> <mlm T|F>
# run dir $T/runs/<name> from the kept rt_plain control_p8 run (as meterproto/stage_run.sh: native output every 6 h,
# meter + hook on); prints the job id
set -e
M=/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm/trace
name=$1; exe=$2; mods=$3; bp=$4; ml=$5
S=$M/rt_plain/stmp/apera/FV3_RT/rt_3544740/control_p8_intel
[ -d "$S" ] || { echo "no template"; exit 1; }
D=$T/runs/$name
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
printf '\n&budget_nml\n  budget_meter = .true.\n  budget_hook = .true.\n  budget_probe = .%s.\n/\n' $( [ $bp = T ] && echo true || echo false ) >> input.nml
grep -q '^  isatmedmf    = 1$' input.nml || { echo "ABORT no isatmedmf line"; exit 1; }
sed -i "s/^  isatmedmf    = 1$/&\n  mlm          = .$( [ $ml = T ] && echo true || echo false )./" input.nml
cp $exe fv3.exe
cp $mods modulefiles/modules.fv3.lua
cp $(dirname $mods)/../modulefiles/ufs_common.lua modulefiles/ 2>/dev/null || true
sed -i -e "/^#SBATCH/ s/--job-name=[^ ]*/--job-name=tr_$name/" -e "/^#SBATCH -J/ s/-J [^ ]*/-J tr_$name/" job_card
grep -q "$S" job_card && { echo "ABORT: job_card references the template dir"; exit 1; }
echo "$name: exe=$exe $(grep -A4 budget_nml input.nml | tr -s ' ' | tr '\n' ' ') $(grep -E '^ *(mlm|isatmedmf|ccpp_suite) ' input.nml | tr -s ' ' | tr '\n' ' ') threads=$(grep omp_num ufs.configure | tr -s ' ')" >&2
sbatch --parsable job_card
