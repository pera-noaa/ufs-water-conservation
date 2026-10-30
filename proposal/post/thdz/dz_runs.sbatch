#!/bin/bash
#SBATCH -A co2 -p hercules -q batch --exclusive -N 12 -t 01:30:00 -J r_dz
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites/logs/runs_r_dz.%j.log
# Thompson density/layer-depth forms: dzO (ours), dzB (density fix reverted), dzA (alternative); p8_mynn and rap, 24 h
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
set -eu
RUNS=""
for t in dzO dzB dzA; do
  [ -s $S/exe/$t.exe ] || { echo "NO EXE $t"; exit 1; }
  bash $S/tools/mkrun.sh ${t}_mynn $t control_p8_mynn; bash $S/tools/mkrun.sh ${t}_rap $t rap_control
  RUNS="$RUNS ${t}_mynn ${t}_rap"
done
set +eu
r0=$(echo $RUNS | cut -d' ' -f1)
cd $S/runs/$r0
MACHINE_ID=hercules; source ./module-setup.sh; module use $PWD/modulefiles; module load modules.fv3
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
