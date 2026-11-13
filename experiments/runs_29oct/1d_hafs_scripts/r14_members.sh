#!/bin/bash
# r14_members.sh: 20 members per arm (consv_te 1, 0.999 ... 0.981 in input.nml, as hafs_samf/q_ens3.sh), alternating arms;
# TAG suffixes the dir/job names (run 1, TAG empty, failed: the moving nest rewrites grid_mspec*.nc, symlinked read-only);
# small files and grid_mspec*.nc copied from r14_1d/tpl, inputs symlinked to it (read-only), exe symlinked; then the stats job
set -eu
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; P=$U/pr1; R=$P/r14_1d; T=$R/tpl; SC=$P/r14_1d_scripts
ids=""
for v in $(seq 1000 -1 981); do for a in a b; do
  d=$R/${a}${TAG:-}_c$v; [ -e $d ] && { echo "GATE: $d exists"; exit 1; }; mkdir $d
  for e in $T/*; do n=${e##*/}
    case $n in input.nml|input_nest02.nml|model_configure|ufs.configure|diag_table|field_table|job_card|fd_ufs.yaml|module-setup.sh|fv3_run|data_table) cp -p $e $d/;;
      modulefiles) cp -rp $e $d/;; grid_mspec*) cp $e $d/ && chmod u+w $d/$n;; RESTART) mkdir $d/RESTART;; *) ln -s $e $d/$n;; esac
  done
  ln -s $R/wm/tests/fv3_hafs1d$a.exe $d/fv3.exe
  [ $v = 1000 ] || sed -i "s/^\( *\)consv_te = 1\.$/\1consv_te = 0.$v/" $d/input.nml
  cv=$( [ $v = 1000 ] && echo 1. || echo 0.$v)
  [ "$(grep -c "consv_te = $cv\$" $d/input.nml)" = 1 ] && grep -q "consv_te = 0\.$" $d/input_nest02.nml || { echo "GATE: consv_te $d"; exit 1; }
  sed -i -e "s/^#SBATCH --account=.*/#SBATCH --account=co2/" -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"r14_${a}${TAG:-}_c$v\"/" $d/job_card
  grep -q "^#SBATCH --account=co2$" $d/job_card && grep -q "^#SBATCH --qos=batch$" $d/job_card && grep -q "^#SBATCH --partition=hercules$" $d/job_card || { echo "GATE: job_card $d"; exit 1; }
  j=$(cd $d && sbatch --parsable job_card); ids="$ids:$j"
  echo "$a${TAG:-} c$v $(md5sum $d/fv3.exe | cut -c1-8) consv_te $cv job $j"
done; done
s=$(sbatch --parsable -A co2 -p hercules -q batch -n 1 -t 00:30:00 -J r14_1d_stats --dependency=afterany$ids -o $R/stats${TAG:-}.%j.log --export=ALL,TAG=${TAG:-} $SC/r14_stats.sh)
echo "stats job $s"; echo MEMBERS_SUBMITTED
