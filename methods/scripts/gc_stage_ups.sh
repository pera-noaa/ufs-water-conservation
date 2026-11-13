#!/bin/bash
# Upstream gc* run dir (copy of upstream/stage_budget_run2.sh with HOURS and a guarded rm): gc_stage_ups.sh <tag> <tests_dir> <exe_name> <kept_rt_rundir> [HOURS=50] [wall=40]
set -e
tag=${1:?tag}; T=${2:?tests}; exe=${3:?exe}; S=${4:?rundir}; H=${5:-50}; wall=${6:-40}
case "$tag" in gc*) ;; *) echo "tag must start with gc"; exit 1;; esac
B=/work2/noaa/co2/ash/ufs-chem-v1/upstream
[ -x $T/$exe.exe ] || { echo "missing $T/$exe.exe"; exit 1; }
[ -d $S ] || { echo "missing rundir $S"; exit 1; }
D=$B/rt/wbgc_$tag
[ -e "$D" ] && { echo "exists: $D"; exit 1; }
mkdir -p "${D:?}/RESTART" "$D/modulefiles"
cd $S
for e in *; do
  case "$e" in atmf*|sfcf*|GFS*|RESTART|out|err|PET*|logfile*|log.atm*|ESMF_Profile*|job_timestamp.txt|warnfile*|*.log|input.nml|model_configure|diag_table|job_card|fv3.exe|modulefiles) ;;
    *) ln -s "$S/$e" "$D/$e";; esac
done
cp $S/input.nml $S/model_configure $S/diag_table $S/job_card $D/
cd $D
fh=$(seq 0 24 "$H" | paste -sd" ")
sed -i -e 's|^output_grid: .*|output_grid:             cubed_sphere_grid|' -e 's|^write_dopost: .*|write_dopost:            .false.|' \
       -e "s|^output_fh: .*|output_fh:               $fh|" -e "s|^restart_interval: .*|restart_interval:        $H|" \
       -e "s|^nhours_fcst: .*|nhours_fcst:             $H|" model_configure
sed -i -e 's/^\( *ldiag3d *= *\).false./\1.true./' -e 's/^\( *qdiag3d *= *\).false./\1.true./' input.nml
for t in qv liq_wat ice_wat rainwat snowwat graupel; do for p in pbl deepcnv shalcnv mp phys nophys; do
  m=gfs_phys; [ $p = nophys ] && m=gfs_dyn
  printf '"%s",  "dtend_%s_%s",  "dtend_%s_%s",  "fv3_history",  "all",  .false.,  "none",  2\n' $m $t $p $t $p >> diag_table
done; done
for t in liq_wat ice_wat rainwat snowwat graupel; do
  printf '"gfs_phys",  "dtend_%s_cnvtrans",  "dtend_%s_cnvtrans",  "fv3_history",  "all",  .false.,  "none",  2\n' $t $t >> diag_table
done
cp $T/$exe.exe fv3.exe
cp $T/modules.$exe.lua modulefiles/modules.fv3.lua
cp $T/../modulefiles/ufs_common.lua modulefiles/
sed -i -e "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"wbgc_$tag\"/" -e "s/^#SBATCH --time=.*/#SBATCH --time=$wall/" job_card
echo "$tag: $D $(grep -E '^(nhours_fcst|output_fh)' model_configure | tr -s ' ' | tr '\n' ' ') $(sbatch job_card)"
