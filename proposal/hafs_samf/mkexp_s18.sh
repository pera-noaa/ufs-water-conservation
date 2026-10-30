#!/bin/bash
# mkexp_s18.sh <group>: rerun q_<group>_L* (progsigma false, 48 h) to 24 h with history at 18 and 24 h, as q_<group>_S*:
# develop's earliest crash is at 19.4 h, so all 10 members reach 18 h. Same exe and namelists as the L run.
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp
g=${1:?group}
for L in $H/q_${g}_L*; do
  v=${L##*_L}; n=q_${g}_S$v
  [ -e $H/$n ] && { echo "$n exists"; continue; }
  cp -a $H/tpl $H/$n && cp $L/fv3.exe $H/$n/fv3.exe && cp $L/input.nml $L/input_nest02.nml $L/field_table $H/$n/ || exit 1
  sed -e "s/^nhours_fcst: .*/nhours_fcst:             24/" -e "s/^output_fh: .*/output_fh:               18 24/" $L/model_configure > $H/$n/model_configure
  sed -e "s/--job-name=\"hx_q_${g}_L$v\"/--job-name=\"hx_$n\"/" -e "s/^#SBATCH --time=120$/#SBATCH --time=60/" $L/job_card > $H/$n/job_card
  [ "$(diff $L/model_configure $H/$n/model_configure | grep -c '^[<>]')" = 4 ] && grep -q "hx_$n" $H/$n/job_card \
    && grep -q "^#SBATCH --time=60$" $H/$n/job_card && cmp -s $L/fv3.exe $H/$n/fv3.exe || { echo "$n: GATE edit"; exit 1; }
  for f in diag_table ufs.configure fd_ufs.yaml input.nml input_nest02.nml field_table; do
    cmp -s $L/$f $H/$n/$f || { echo "$n: GATE $f differs from $L"; exit 1; }; done
  [ "$(cd $L/INPUT && ls -l | tail -n +2 | md5sum)" = "$(cd $H/$n/INPUT && ls -l | tail -n +2 | md5sum)" ] || { echo "$n: GATE INPUT"; exit 1; }
  cd $H/$n && echo "$n $(md5sum fv3.exe | cut -c1-8) $(grep -h -o "consv_te *= *[0-9.]*" input.nml | head -1) job $(sbatch --parsable job_card)"
done
