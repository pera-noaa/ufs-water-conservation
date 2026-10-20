#!/bin/bash
# usage: rt_setup.sh <tree> <RT test> <run name> [NML entries for fv_core_nml] : RT run dir in $W/rtn/<name>
# via a copy of the tree's run_test.sh that stops before job submission; then IC with test tracers, field/diag tables.
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trdyn; DISK=/work2/noaa/epic/hercules/UFS-WM_RT
tree=${1:?}; test=${2:?}; name=${3:?}; shift 3
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
bash run_test_nosub.sh $PR $W/rtn $test $name $tree > $W/rtn/logs/setup_$name.log 2>&1 || { tail -5 $W/rtn/logs/setup_$name.log; exit 1; }
cd $W/rtn/$name
for f in input.nml input_nest02.nml; do
  [ -f $f ] || continue
  for kv in "$@"; do sed -i -E "0,/^&fv_core_nml/s//\&fv_core_nml\n  ${kv}/" $f; done
done
grep -E 'srun|SBATCH' job_card | head -8
echo "RT_OK $W/rtn/$name"
