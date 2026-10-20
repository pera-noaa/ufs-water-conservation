#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 1 -c 8 -t 02:00:00 -J nm12run
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12/logs/run.%x.%j.log
# usage: sbatch -J <tag> --export=ALL,JOBS=<file of run.sh lines> run.sbatch  (lines run 8 at a time)
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12/harness
xargs -P 8 -d '\n' -I{} bash -c "{}" < "$JOBS"
