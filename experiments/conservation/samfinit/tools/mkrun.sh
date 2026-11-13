#!/bin/bash
# usage: mkrun.sh <name> <fv3 exe> <hours> <walltime min> [nml sed expr] ; copy energy control_p8 template, set exe/hours, submit
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/samfinit
name=${1:?name}; exe=${2:?exe}; hrs=${3:?hours}; wall=${4:?wall}; sedx=${5:-}
dst=$C/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
rsync -a --exclude=fv3.exe.ctl64 --exclude=fv3.exe $E/runs/tmpl/ $dst/
cp "$exe" $dst/fv3.exe
cd $dst
rm -f out err
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"s_$name\"/; s/^#SBATCH --time=.*/#SBATCH --time=$wall/" job_card
if [ "$hrs" != 24 ]; then
  sed -i -E "s/^nhours_fcst:.*/nhours_fcst:             $hrs/; s/^output_fh:.*/output_fh:               0 $hrs/; s/^restart_interval:.*/restart_interval:        0/" model_configure
fi
if [ -n "$sedx" ]; then sed -i -E "$sedx" input.nml; fi
sbatch job_card
