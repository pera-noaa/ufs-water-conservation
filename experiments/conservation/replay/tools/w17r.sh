#!/bin/bash
# usage: w17r.sh : water diff 17r check on ccpp-physics @242a2fc (develop @112b1d46): dev + water 01-16 (-p1 -F0), then
# 17r and 18 at -F0; reference arm with the original 17; known-bads: 17r on top of 17, 17r on bare develop.
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay; W=$R/w17r; WA=$W/water
ap() { (cd $1 && patch -p1 -F0 --no-backup-if-mismatch ${3:-} < $2) > $W/last.log 2>&1; rc=$?
  echo "  $(basename $2) on $(basename $1): $([ $rc = 0 ] && echo applies || echo FAILS) (offsets $(grep -c '(offset' $W/last.log), failed hunks $(grep -c 'Hunk #[0-9]* FAILED' $W/last.log))"; return $rc; }
mk() { rm -rf "${W:?}/$1"; rsync -a $W/dev/ $W/$1/; }
mk w16; for f in $(ls $WA | grep -E '^(0[1-9]|1[0-6])_' | sort); do ap $W/w16 $WA/$f > /dev/null || { echo "ABORT $f"; exit 1; }; done
echo "dev + water 01-16: $(ls $WA | grep -c -E '^(0[1-9]|1[0-6])_') diffs applied at -F0"
echo "arm 17r:"; mk a17r; rsync -a $W/w16/ $W/a17r/; ap $W/a17r $WA/17r_NM10r_noahmp_precip_phase.diff; ap $W/a17r $WA/18_NM11_noahmp_ground_vapour_latent_heat.diff
echo "reference arm 17:"; mk a17; rsync -a $W/w16/ $W/a17/; ap $W/a17 $WA/17_NM10_noahmp_precip_phase.diff; ap $W/a17 $WA/18_NM11_noahmp_ground_vapour_latent_heat.diff
echo "known-bad: 17r after 17 (dry run):"; mk kb1; rsync -a $W/w16/ $W/kb1/; ap $W/kb1 $WA/17_NM10_noahmp_precip_phase.diff >/dev/null; ap $W/kb1 $WA/17r_NM10r_noahmp_precip_phase.diff --dry-run
echo "known-bad: 17r on bare develop (dry run):"; ap $W/dev $WA/17r_NM10r_noahmp_precip_phase.diff --dry-run
echo "17r arm vs 17 arm, files differing:"; diff -rq $W/a17r $W/a17 | sed "s#$W/##g"
for d in w16 a17 kb1; do rm -rf "${W:?}/$d"; done
