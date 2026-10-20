#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 3 --ntasks-per-node=80 --exclusive
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn/logs/nest_%x.%j.log
# usage: sbatch -J <id> -t <min> --export=ALL,RUNS="<run> ..." multirun.sbatch ; runs $W/rt/<run> one after another
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn
for r in $RUNS; do
  cd $W/rtn/$r || { echo "RUN_EXIT $r nodir"; continue; }
  (
    set +x
    MACHINE_ID=hercules
    source ./module-setup.sh
    module use $PWD/modulefiles
    module load modules.fv3
    set +eu
    ulimit -s unlimited
    export OMP_STACKSIZE=512M KMP_AFFINITY=scatter OMP_NUM_THREADS=1 PMI2="" I_MPI_EXTRA_FILESYSTEM=ON FI_MLX_INJECT_LIMIT=0
    [ -f pre.sh ] && bash ./pre.sh
    source ./env.sh
    t0=$(date +%s)
    srun --label --distribution=block:block -n 240 ./fv3.exe > out 2> err
    rc=$?
    echo "RUN_EXIT $r rc=$rc sec=$(( $(date +%s) - t0 ))"
  )
  rm -f $W/rtn/$r/PET*.ESMF_LogFile
done
