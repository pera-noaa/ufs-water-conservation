#!/bin/bash
#SBATCH -A co2 -p hercules -q batch --exclusive -t 01:15:00
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/logs/runs_%x.%j.log
# usage: sbatch -J <tag> -N <2*nruns> --export=ALL,RUNS="<run> ..." runs.sbatch   (2 nodes, 150 tasks per run)
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
set -x
r0=$(echo $RUNS | cut -d' ' -f1)
cd $S/runs/$r0
set +x; MACHINE_ID=hercules; source ./module-setup.sh; module use $PWD/modulefiles; module load modules.fv3; set -x
ulimit -s unlimited
export OMP_STACKSIZE=512M KMP_AFFINITY=scatter OMP_NUM_THREADS=1 I_MPI_EXTRA_FILESYSTEM=ON FI_MLX_INJECT_LIMIT=0
for r in $RUNS; do
  ( cd $S/runs/$r && source ./sm_env && date -Is > t0 && \
    srun --exact --nodes=2 --ntasks=150 --cpu-bind=cores ./fv3.exe > out 2> err; echo "rc=$?" > rc; date -Is > t1 ) &
  sleep 2
done
wait
for r in $RUNS; do echo "$r $(cat $S/runs/$r/rc) $(grep -c '^SMS' $S/runs/$r/out) $(ls $S/runs/$r/atmf024* 2>/dev/null | wc -l)"; done
echo RUNS_DONE
