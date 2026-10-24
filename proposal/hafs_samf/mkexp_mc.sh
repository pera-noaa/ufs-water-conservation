#!/bin/bash
# mkexp_mc.sh <name> <exe> <sed expr for model_configure> [sed expr for input.nml and input_nest02.nml]:
# mkexp.sh with a model_configure edit (e.g. dt_atmos). Prints name, the edited lines and the job id.
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp
n=${1:?name}; exe=${2:?exe}; mc=${3:?model_configure sed}; ed=${4:-}
[ -e $H/$n ] && { echo "$n exists"; exit 1; }
[ -f $exe ] || { echo "no exe $exe"; exit 1; }
cp -a $H/tpl $H/$n && cp $exe $H/$n/fv3.exe || exit 1
sed -i "$mc" $H/$n/model_configure
[ -n "$ed" ] && sed -i "$ed" $H/$n/input.nml $H/$n/input_nest02.nml
cmp -s $H/tpl/model_configure $H/$n/model_configure && { echo "$n: model_configure unchanged"; exit 1; }
sed -i "s/--job-name=\"run_hafs_global_1nest_atm_intel\"/--job-name=\"hx_$n\"/" $H/$n/job_card
cd $H/$n && echo "$n $(md5sum fv3.exe | cut -c1-8) $(diff $H/tpl/model_configure model_configure | grep '^>' | tr -s ' ' | tr '\n' ' ') $( [ -n "$ed" ] && grep -h -o "consv_te *= *[0-9.]*" input.nml input_nest02.nml | tr "\n" " ") job $(sbatch --parsable job_card)"
