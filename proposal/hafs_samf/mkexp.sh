#!/bin/bash
# mkexp.sh <name> <bis tree letter or path to exe> [output_fh list] [sed expr for input.nml and input_nest02.nml]
# copies tpl/, installs the exe, optionally edits output_fh and the namelists, submits job_card. Prints name and job id.
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp; P=${H%/hafs_exp}
n=${1:?name}; x=${2:?exe}; fh=${3:-}; ed=${4:-}
[ -e $H/$n ] && { echo "$n exists"; exit 1; }
case $x in /*) exe=$x;; *) exe=$P/bis$x/tests/fv3_hafsw_intel.exe;; esac
[ -f $exe ] || { echo "no exe $exe"; exit 1; }
cp -a $H/tpl $H/$n && cp $exe $H/$n/fv3.exe || exit 1
[ -n "$fh" ] && sed -i "s/^output_fh: .*/output_fh:               $fh/" $H/$n/model_configure
[ -n "$ed" ] && sed -i "$ed" $H/$n/input.nml $H/$n/input_nest02.nml
sed -i "s/--job-name=\"run_hafs_global_1nest_atm_intel\"/--job-name=\"hx_$n\"/" $H/$n/job_card
cd $H/$n && echo "$n $(md5sum fv3.exe | cut -c1-8) $(grep "^output_fh" model_configure | tr -s " ") $( [ -n "$ed" ] && grep -h -o "consv_te *= *[0-9.]*" input.nml input_nest02.nml | tr "\n" " ") job $(sbatch --parsable job_card)"
