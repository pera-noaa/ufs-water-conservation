#!/bin/bash
#SBATCH -A co2
#SBATCH -p hercules
#SBATCH -q batch
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=80
#SBATCH --exclusive
#SBATCH --time=60
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/dycred/logs/%x.%j.out
# usage: sbatch -J name runcases.sbatch case1 case2 ... (runs each case's job_card in turn)
D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/dycred
for c in "$@"; do
  cd $D/runs/$c || continue
  echo "$(date +%T) start $c"
  bash ./job_card > out 2> err
  echo "$(date +%T) end $c rc=$? ENG=$(grep -c 'ENG Deficit' out)"
done
