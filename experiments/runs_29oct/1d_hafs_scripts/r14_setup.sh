#!/bin/bash
# r14_setup.sh (login node, git + rsync only): WM copy for the 1d HAFS rerun; fetch the track branches; static gates
set -eu
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; P=$U/pr1; S=$P/series; R=$P/r14_1d; W=$R/wm; PH=UFSATM/ccpp/physics
[ -e $R ] && { echo "GATE: $R exists"; exit 1; }
mkdir $R
nice rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/rettime/wm/ $W/
[ "$(git -C $W rev-parse --short=8 HEAD)" = 783f524a ] || { echo "GATE: wm copy not at 783f524a"; exit 1; }
git -C $W fetch -q --no-recurse-submodules $S +refs/heads/pr1-0b:refs/heads/pr1-0b
git -C $W/UFSATM fetch -q --no-recurse-submodules $S/UFSATM +refs/heads/pr1-0b:refs/heads/pr1-0b
git -C $W/$PH fetch -q --no-recurse-submodules $S/$PH +refs/heads/pr1-0b:refs/heads/pr1-0b \
  +refs/heads/pr1-seaice_nsst:refs/heads/pr1-seaice_nsst +refs/heads/pr1-xlamue:refs/heads/pr1-xlamue
git -C $W checkout -q pr1-0b
git -C $W/UFSATM checkout -q --detach pr1-0b
git -C $W/$PH checkout -q --detach pr1-0b
echo "wm $(git -C $W rev-parse --short=8 HEAD) ufsatm $(git -C $W/UFSATM rev-parse --short=8 HEAD) physics $(git -C $W/$PH rev-parse --short=8 HEAD)"
echo "branch heads: 0b $(git -C $W/$PH rev-parse --short=8 pr1-0b) seaice_nsst $(git -C $W/$PH rev-parse --short=8 pr1-seaice_nsst) xlamue $(git -C $W/$PH rev-parse --short=8 pr1-xlamue)"
[ "$(git -C $W/$PH rev-parse pr1-xlamue)" = ce5d4d04575748df64e6471dc190a1d2d2e9d036 ] || { echo "GATE: xlamue head"; exit 1; }
[ "$(git -C $W/$PH rev-parse pr1-seaice_nsst)" = "$(git -C $P/q/t1a/$PH rev-parse 9528cfc6^2)" ] || { echo "GATE: seaice_nsst != the branch merged in q/t1a"; exit 1; }
echo "wm 783f524a..pr1-0b: $(git -C $W diff --name-only 783f524a HEAD | tr '\n' ' ')"
[ "$(git -C $W rev-parse HEAD:UFSATM)" = "$(git -C $W/UFSATM rev-parse HEAD)" ] || { echo "GATE: wm gitlink != ufsatm"; exit 1; }
[ "$(git -C $W/UFSATM rev-parse HEAD:ccpp/physics)" = "$(git -C $W/$PH rev-parse HEAD)" ] || { echo "GATE: ufsatm gitlink != physics"; exit 1; }
bad=$( { git -C $W submodule status; git -C $W/UFSATM submodule status; git -C $W/$PH submodule status; } | grep -v '^ ' || true)
[ -z "$bad" ] || { echo "GATE: submodules off their gitlinks:"; echo "$bad"; exit 1; }
[ -z "$(git -C $W/$PH status --porcelain)" ] && [ -z "$(git -C $W/UFSATM status --porcelain)" ] || { echo "GATE: dirty"; exit 1; }
F3="physics/SFC_Models/SeaIce/CICE/sfc_sice.f physics/SFC_Models/SeaIce/CICE/sfc_sice.meta physics/SFC_Layer/UFS/sfc_nst.f90"
[ "$(git -C $W/$PH diff --name-only d9b70feb pr1-seaice_nsst | sort | tr '\n' ' ')" = "$(echo $F3 | tr ' ' '\n' | sort | tr '\n' ' ')" ] || { echo "GATE: 1d files"; exit 1; }
git -C $W/$PH diff --quiet d9b70feb pr1-0b -- $F3 || { echo "GATE: 0b touches the 1d files"; exit 1; }
git -C $W/$PH diff --quiet 9b65688c pr1-0b -- $F3 || { echo "GATE: 0b base differs on the 1d files"; exit 1; }
git -C $W/$PH diff --quiet d9b70feb 9b65688c -- $F3 || { echo "GATE: ufs/dev moved the 1d files since d9b70feb"; exit 1; }
git -C $W/$PH merge-base --is-ancestor 9b65688c pr1-0b || { echo "GATE: 0b not on 9b65688c"; exit 1; }
echo "static gates pass"
nice rsync -a $P/hafs_exp/tpl/ $R/tpl/
for f in input.nml input_nest02.nml model_configure ufs.configure diag_table field_table; do
  cmp -s $R/tpl/$f $P/rt_x0b/stmp/apera/FV3_RT/rt_2084754/hafs_global_1nest_atm_intel/$f || echo "NOTE: tpl $f differs from rt_x0b"
done
echo "tpl $(du -sh $R/tpl | cut -f1); wm $(du -sh $W | cut -f1)"
echo SETUP_DONE
