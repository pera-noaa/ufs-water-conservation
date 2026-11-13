#!/bin/bash
# mkcase.sh <name> <exe> <hours> <na_init> [sed expr for input.nml ...] : make a run dir (no submit)
set -euo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; D=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/dycred
name=${1:?}; exe=${2:?}; hrs=${3:?}; nai=${4:?}; shift 4
dst=$D/runs/$name
[ -e "$dst" ] && { echo "ABORT: $dst exists"; exit 1; }
mkdir -p $D/runs
rsync -a --exclude=fv3.exe.ctl64 --exclude=fv3.exe --exclude=RESTART $E/runs/tmpl/ $dst/
mkdir $dst/RESTART
cp "$exe" $dst/fv3.exe
cd $dst
for f in input.nml job_card model_configure diag_table field_table; do
  [ -L $f ] && cp --remove-destination "$(readlink -f $f)" $f
  [ -L $f ] && { echo "ABORT: $f still a link"; exit 1; }
done
sed -i -E "s/^nhours_fcst:.*/nhours_fcst:             $hrs/; s/^output_fh:.*/output_fh:               $hrs/" model_configure
sed -i -E "s/^(\s*print_freq\s*=\s*).*/\1-1/; s/^(\s*na_init\s*=\s*).*/\1$nai/" input.nml
for x in "$@"; do sed -i -E "$x" input.nml; done
grep -q "print_freq = -1" input.nml || { echo "ABORT: print_freq"; exit 1; }
echo "$name hrs=$hrs na_init=$nai exe=$(md5sum fv3.exe | cut -c1-8) $*" > case.info
cat case.info
