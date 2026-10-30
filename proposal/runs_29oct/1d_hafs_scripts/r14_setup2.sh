#!/bin/bash
# r14_setup2.sh: resume r14_setup.sh after the dirty gate: restore the tracked build_* files rsync's exclude dropped, rerun gates, tpl
set -eu
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; P=$U/pr1; S=$P/series; R=$P/r14_1d; W=$R/wm; PH=UFSATM/ccpp/physics
[ -e $R/tpl ] && { echo "GATE: tpl exists"; exit 1; }
git -C $W submodule foreach -q --recursive 'c=$(git status --porcelain --ignore-submodules=all | grep -v "^ D " || true); [ -z "$c" ] || { echo "GATE: $displaypath non-deletion: $c"; exit 1; }; git checkout -q -- . ' || exit 1
bad=$( { git -C $W submodule status; git -C $W/UFSATM submodule status; git -C $W/$PH submodule status; } | grep -v '^ ' || true)
[ -z "$bad" ] || { echo "GATE: submodules off their gitlinks:"; echo "$bad"; exit 1; }
[ -z "$(git -C $W/$PH status --porcelain)" ] && [ -z "$(git -C $W/UFSATM status --porcelain)" ] || { echo "GATE: dirty"; git -C $W/UFSATM status --porcelain; exit 1; }
echo "wm status: $(git -C $W status --porcelain | grep -v '^??' | tr '\n' ' ')"
F3="physics/SFC_Models/SeaIce/CICE/sfc_sice.f physics/SFC_Models/SeaIce/CICE/sfc_sice.meta physics/SFC_Layer/UFS/sfc_nst.f90"
[ "$(git -C $W/$PH diff --name-only d9b70feb pr1-seaice_nsst | sort | tr '\n' ' ')" = "$(echo $F3 | tr ' ' '\n' | sort | tr '\n' ' ')" ] || { echo "GATE: 1d files"; exit 1; }
git -C $W/$PH diff --quiet d9b70feb pr1-0b -- $F3 || { echo "GATE: 0b touches the 1d files"; exit 1; }
git -C $W/$PH diff --quiet 9b65688c pr1-0b -- $F3 || { echo "GATE: 0b base differs on the 1d files"; exit 1; }
git -C $W/$PH diff --quiet d9b70feb 9b65688c -- $F3 || { echo "GATE: ufs/dev moved the 1d files since d9b70feb"; exit 1; }
git -C $W/$PH merge-base --is-ancestor 9b65688c pr1-0b || { echo "GATE: 0b not on 9b65688c"; exit 1; }
echo "static gates pass"
nice rsync -a $P/hafs_exp/tpl/ $R/tpl/
X=$P/rt_x0b/stmp/apera/FV3_RT/rt_2084754/hafs_global_1nest_atm_intel
for f in input.nml input_nest02.nml model_configure ufs.configure diag_table field_table fd_ufs.yaml module-setup.sh fv3_run modulefiles/modules.fv3.lua; do
  cmp -s $R/tpl/$f $X/$f && echo "tpl $f = rt_x0b" || echo "NOTE: tpl $f differs from rt_x0b"
done
ls $R/tpl/modulefiles
echo "tpl $(du -sh $R/tpl | cut -f1); wm $(du -sh $W | cut -f1)"
echo SETUP_DONE
