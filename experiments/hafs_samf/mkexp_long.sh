#!/bin/bash
# mkexp_long.sh <name> <exe> <hours> [sed expr for input.nml and input_nest02.nml]: mkexp.sh for a longer forecast
# (history at 24 h and at the end, 120 min wall). Prints name and job id.
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp
n=${1:?name}; exe=${2:?exe}; hr=${3:?hours}; ed=${4:-}
[ -e $H/$n ] && { echo "$n exists"; exit 1; }
[ -f $exe ] || { echo "no exe $exe"; exit 1; }
cp -a $H/tpl $H/$n && cp $exe $H/$n/fv3.exe || exit 1
sed -i -e "s/^nhours_fcst: .*/nhours_fcst:             $hr/" -e "s/^output_fh: .*/output_fh:               24 $hr/" $H/$n/model_configure
[ -n "$ed" ] && sed -i "$ed" $H/$n/input.nml $H/$n/input_nest02.nml
sed -i -e "s/--job-name=\"run_hafs_global_1nest_atm_intel\"/--job-name=\"hx_$n\"/" -e "s/^#SBATCH --time=30$/#SBATCH --time=120/" $H/$n/job_card
grep -q "^nhours_fcst: *$hr$" $H/$n/model_configure && grep -q "^#SBATCH --time=120$" $H/$n/job_card || { echo "$n: edit failed"; exit 1; }
cd $H/$n && echo "$n $(md5sum fv3.exe | cut -c1-8) $(grep "^output_fh" model_configure | tr -s " ") $( [ -n "$ed" ] && grep -h -o "consv_te *= *[0-9.]*" input.nml input_nest02.nml | tr "\n" " ") job $(sbatch --parsable job_card)"
