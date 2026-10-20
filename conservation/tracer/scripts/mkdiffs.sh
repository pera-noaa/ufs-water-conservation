#!/bin/bash
# Make the deliverable diffs from base vs tm (meters+hook) and tm vs tmf (FV2). Output in $T/diffs.
T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer; O=$T/diffs; mkdir -p $O
B=$T/base/UFSATM; M=$T/tm/UFSATM; F=$T/tmf/UFSATM
d() { # base-root mod-root relpath label-prefix-root
  diff -uN --label "a/$3" --label "b/$3" "$1/$3" "$2/$3"; }
( cd $B/ccpp && d $B/ccpp $M/ccpp data/CCPP_typedefs.F90 ) > $O/01_testhook_chem_pbl_UFSATM-ccpp.diff
: > $O/02_meters_ccpp-physics.diff
for f in physics/Interstitials/UFS_SCM_NEPTUNE/tm_meter.F90 \
         physics/Interstitials/UFS_SCM_NEPTUNE/GFS_DCNV_generic_post.F90 physics/Interstitials/UFS_SCM_NEPTUNE/GFS_DCNV_generic_post.meta \
         physics/Interstitials/UFS_SCM_NEPTUNE/GFS_SCNV_generic_post.F90 physics/Interstitials/UFS_SCM_NEPTUNE/GFS_SCNV_generic_post.meta \
         physics/Interstitials/UFS_SCM_NEPTUNE/GFS_GWD_generic_post.F90 physics/Interstitials/UFS_SCM_NEPTUNE/GFS_GWD_generic_post.meta \
         physics/CONV/SAMF/samfdeepcnv.f; do
  d $B/ccpp/physics $M/ccpp/physics $f >> $O/02_meters_ccpp-physics.diff; done
: > $O/03_meters_fv3.diff
for f in model/fv_dynamics.F90 driver/UFS/atmosphere.F90; do
  d $B/fv3/atmos_cubed_sphere $M/fv3/atmos_cubed_sphere $f >> $O/03_meters_fv3.diff; done
# FV2 alone, against the base tree (applies on top of 19_FV1)
cp $B/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90 $O/atm_base.F90
/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I $T/bin/fix_FV2_statein_dp.py $O/fv2tree >/dev/null 2>&1 || true
mkdir -p $O/fv2/UFSATM/fv3/atmos_cubed_sphere/driver/UFS
cp $O/atm_base.F90 $O/fv2/UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90
/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I $T/bin/fix_FV2_statein_dp.py $O/fv2 >/dev/null
d $B/fv3/atmos_cubed_sphere $O/fv2/UFSATM/fv3/atmos_cubed_sphere driver/UFS/atmosphere.F90 > $O/01_FV2_fv3_statein_consistent_layer_mass.diff
rm -rf "${O:?}/fv2" "${O:?}/atm_base.F90"
wc -l $O/*.diff
# T1 causal test hook (SAMF deep sub-stepping), relative to the metered tree
d $M/ccpp/physics $T/tms/UFSATM/ccpp/physics physics/CONV/SAMF/samfdeepcnv.f > $O/04_testhook_samf_substep_ccpp-physics.diff
wc -l $O/04_*.diff
