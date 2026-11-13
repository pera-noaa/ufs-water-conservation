#!/bin/bash
#SBATCH -A co2 -p hercules -q batch --exclusive -t 01:30:00 -N 4
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/logs/rs_%x.%j.log
# usage: sbatch -J <tag> --export=ALL,NAME=<name> rs.sbatch   (after mkrs.sh)
S0=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/runs
set -x
cd $S0/${NAME}_S
set +x; MACHINE_ID=hercules; source ./module-setup.sh; module use $PWD/modulefiles; module load modules.fv3; set -x
ulimit -s unlimited
export OMP_STACKSIZE=512M KMP_AFFINITY=scatter OMP_NUM_THREADS=1 I_MPI_EXTRA_FILESYSTEM=ON FI_MLX_INJECT_LIMIT=0
run() { ( cd $S0/$1 && source ./sm_env && srun --exact --nodes=2 --ntasks=150 --cpu-bind=cores ./fv3.exe > out 2> err; echo "rc=$?" > rc ); }
run ${NAME}_S & sleep 2; run ${NAME}_L & wait %1
cd $S0/${NAME}_R
for f in $S0/${NAME}_S/RESTART/20210322.180000.*; do cp --remove-destination "$f" INPUT/"$(basename "$f" | sed 's/^20210322\.180000\.//')"; done
ls INPUT | grep -c res
run ${NAME}_R
wait
for x in S L R; do echo "$x $(cat $S0/${NAME}_$x/rc)"; done
echo RS_DONE
