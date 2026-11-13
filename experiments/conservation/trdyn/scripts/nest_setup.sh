#!/bin/bash
# usage: nest_setup.sh <tree> <run name> [NML entries for fv_core_nml of both grids] : gnv1_nested run dir in $W/rtn/<name>
# via a copy of the tree's run_test.sh that stops before job submission; then IC with test tracers, field/diag tables.
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trdyn; DISK=/work2/noaa/epic/hercules/UFS-WM_RT
tree=${1:?}; name=${2:?}; shift 2
PR=$W/$tree/tests; mkdir -p $W/rtn $W/rtn/logs
[ -e $W/rtn/$name ] && { echo "ABORT exists"; exit 1; }
sed -e 's/^\( *\)submit_and_wait job_card/\1echo SKIP_SUBMIT/' $PR/run_test.sh > $PR/run_test_nosub.sh
grep -q SKIP_SUBMIT $PR/run_test_nosub.sh
cat > $W/rtn/run_test_$name.env <<ENV
export TEST_ID=$name
export MACHINE_ID=hercules
export RT_COMPILER=intel
export RTPWD=$DISK/NEMSfv3gfs/develop-20260921
export INPUTDATA_ROOT=$DISK/NEMSfv3gfs/input-data-20260617
export INPUTDATA_ROOT_WW3=$DISK/NEMSfv3gfs/input-data-20260617/WW3_input_data_20260811
export PATHRT=$PR
export PATHTR=$W/$tree
export NEW_BASELINE=
export CREATE_BASELINE=false
export RT_SUFFIX=
export BL_SUFFIX=
export SCHEDULER=slurm
export ACCNR=co2
export QUEUE=batch
export PARTITION=hercules
export ROCOTO=false
export ECFLOW=false
export REGRESSIONTEST_LOG=$W/rtn/logs/rt.log
export LOG_DIR=$W/rtn/logs
export DEP_RUN=
export skip_check_results=true
export RTVERBOSE=false
export delete_rundir=false
export WLCLK=30
export DRY_RUN=false
ENV
cd $PR
bash run_test_nosub.sh $PR $W/rtn gnv1_nested $name $tree > $W/rtn/logs/setup_$name.log 2>&1 || { tail -5 $W/rtn/logs/setup_$name.log; exit 1; }
cd $W/rtn/$name
for f in gfs_data.tile1.nc gfs_data.tile2.nc gfs_data.tile3.nc gfs_data.tile4.nc gfs_data.tile5.nc gfs_data.tile6.nc gfs_data.nest02.tile7.nc; do
  rm -f INPUT/$f; ln -s $W/ic_n/$f INPUT/$f; done
for t in pt_udry pt_udry_nopbl pt_umoist_nopbl; do
  u='       "tracer_usage", "chemistry"\n'; [ $t = pt_umoist_nopbl ] && u=''
  printf ' "TRACER", "atmos_mod", "%s"\n           "longname",     "test tracer"\n           "units",        "kg/kg"\n'"$u"'       "profile_type", "fixed", "surface_value=0.0" /\n' $t >> field_table
  printf '"gfs_dyn",     "%s",  "%s",  "fv3_history",    "all",  .false.,  "none",  2\n' $t $t >> diag_table
done
for f in input.nml input_nest02.nml; do
  for kv in "$@"; do sed -i -E "0,/^&fv_core_nml/s//\&fv_core_nml\n  ${kv}/" $f; done
  sed -i -E 's/^(\s*fscav_aero\s*=\s*).*/\1"*:0.0"/' $f
done
grep -E 'srun|SBATCH' job_card | head -8
echo "NEST_OK $W/rtn/$name"
