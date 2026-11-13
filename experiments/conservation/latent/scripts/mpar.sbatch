#!/bin/bash
#SBATCH -A co2 -p hercules -q batch --ntasks-per-node=80 --exclusive
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent/logs/run_%x.%j.log
# usage: sbatch -J <id> -N <2*width> -t <min> --export=ALL,RUNS="<run> ..." mpar.sbatch ; runs $L/rt/<run>, width = N/2 at a time, 2 nodes each
L=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/latent
W=$(( SLURM_JOB_NUM_NODES / 2 ))
for r in $RUNS; do
  while [ $(jobs -rp | wc -l) -ge $W ]; do wait -n; done
  (
    cd $L/rt/$r || { echo "RUN_EXIT $r nodir"; exit 0; }
    set +x
    MACHINE_ID=hercules
    source ./module-setup.sh
    module use $PWD/modulefiles
    module load modules.fv3
    set +eu
    ulimit -s unlimited
    export OMP_STACKSIZE=512M KMP_AFFINITY=scatter OMP_NUM_THREADS=1 PMI2="" I_MPI_EXTRA_FILESYSTEM=ON FI_MLX_INJECT_LIMIT=0
    source ./env.sh
    t0=$(date +%s)
    srun --exclusive -N 2 -n 160 --label --distribution=block:block ./fv3.exe > out 2> err
    rc=$?
    echo "RUN_EXIT $r rc=$rc sec=$(( $(date +%s) - t0 ))"
    rm -f PET*.ESMF_LogFile
  ) &
  sleep 2
done
wait
