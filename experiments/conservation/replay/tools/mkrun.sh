#!/bin/bash
# usage: mkrun.sh <name> <exe> : run dir $R/runs/<name> = energy's run template (copied) + rs13_S's own config files
# (input.nml, model_configure, job_card, field_table, diag_table: the full13 all-on 24 h run with a 12 h restart),
# with <exe> as fv3.exe; submits it. Compare against $E/runs/rs13_S (atmf*.nc, sfcf*.nc, RESTART at 24 h).
set -euo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay; E=$R/../energy; S=$E/runs/${SRCRUN:-rs13_S}
D=$R/runs/${1:?name}; X=${2:?exe}
[ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
mkdir -p $R/runs; rsync -a --exclude=fv3.exe.ctl64 $E/runs/tmpl/ $D/
for f in input.nml model_configure job_card field_table diag_table; do rm -f $D/$f; cp $S/$f $D/$f; done
sed -i -E "s/^#SBATCH --job-name=.*/#SBATCH --job-name=\"$1\"/" $D/job_card
cp "$X" $D/fv3.exe
for f in input.nml model_configure field_table diag_table; do cmp -s $S/$f $D/$f || { echo "ABORT: $f differs"; exit 1; }; done
echo "job_card lines changed: $( (diff $S/job_card $D/job_card || true) | grep -c "^>")"
grep "^#SBATCH" $D/job_card | tr '\n' ' '; echo
cd $D && sbatch job_card
