#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 1 -c 4 -t 00:30:00 -J nm12build
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12/logs/build.%j.log
bash /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12/harness/build.sh
