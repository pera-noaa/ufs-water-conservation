#!/bin/bash
# mkexp_ps.sh <name> <exe> [sed expr for input.nml and input_nest02.nml]: mkexp.sh with progsigma = .true. (as in
# operational HAFS): a sigmab tracer appended to field_table, progsigma and sigmab_coldstart true in both namelists.
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp
n=${1:?name}; exe=${2:?exe}; ed=${3:-}
[ -e $H/$n ] && { echo "$n exists"; exit 1; }
[ -f $exe ] || { echo "no exe $exe"; exit 1; }
cp -a $H/tpl $H/$n && cp $exe $H/$n/fv3.exe || exit 1
printf '%s\n' '# prognostic sigmab tracer' ' "TRACER", "atmos_mod", "sigmab"' '           "longname",     "sigma fraction"' \
  '           "units",        "fraction"' '       "profile_type", "fixed", "surface_value=0.0" /' >> $H/$n/field_table
for f in input.nml input_nest02.nml; do
  sed -i 's/^\( *\)progsigma *= *\.false\./\1progsigma      = .true.\n\1sigmab_coldstart = .true./' $H/$n/$f
  [ "$(grep -c 'progsigma *= *.true.' $H/$n/$f)" = 1 ] && [ "$(grep -c 'sigmab_coldstart *= *.true.' $H/$n/$f)" = 1 ] || { echo "$n: nml edit failed $f"; exit 1; }
done
[ -n "$ed" ] && sed -i "$ed" $H/$n/input.nml $H/$n/input_nest02.nml
sed -i "s/--job-name=\"run_hafs_global_1nest_atm_intel\"/--job-name=\"hx_$n\"/" $H/$n/job_card
cd $H/$n && echo "$n $(md5sum fv3.exe | cut -c1-8) progsigma $(grep -c sigmab field_table) $( [ -n "$ed" ] && grep -h -o "consv_te *= *[0-9.]*" input.nml input_nest02.nml | tr "\n" " ") job $(sbatch --parsable job_card)"
