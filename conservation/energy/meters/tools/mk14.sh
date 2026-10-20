#!/bin/bash
# usage: nohup mk14.sh & : full14/mq14 = full13/mq13 + Ash's decisions (patches/tools/edits14.py), stage snapshots for the
# delta diffs: s0 -> s1 TH8+TH9 unconditional (energy TH8 reversed, held TH8, canopy 03 reversed by content, held TH9),
# s1 -> s2 PL1 folded into EP1, s2 -> s3 NM10r (Noah-MP soil takes the host's convective phase always).
# mq14: preclag lag-meter flag -> EP1 (EM01) + land meter (instrument_land14.py).
# gB14 = gB13 (fx + bug fixes) with energy TH8 -> held TH8 + held TH9 + ensfc2 12_sfc_NM10r; gB14x = the same without
# NM10r (NM10r A/B). fx-cut 13_TH8-TH9 diff and the standalone water diff 17r. All -no-fma. <= 2 own builds.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; A=$E/accepted
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; X=$E/tools/edits14.py
H8=$A/held_TH8_thompson_count_all_surface_sedimentation.diff; H9=$A/held_TH9_thompson_placeholder_not_sedimented.diff
T8=$A/23_energy_06_TH8_thompson_count_all_sedimented_precip.diff; C3=$A/29_canopy_03_TH9_thompson_sed_actual.diff
N10=$A/42_ensfc2_12_sfc_NM10r.diff; cp -p $U/cons/ensfc2/patches/12_sfc_NM10r.diff $N10
FILES="UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90 UFSATM/ccpp/physics/physics/MP/Thompson/mp_thompson.F90
 UFSATM/ccpp/physics/physics/MP/Thompson/mp_thompson.meta UFSATM/ccpp/data/GFS_typedefs.F90 UFSATM/ccpp/data/GFS_typedefs.meta
 UFSATM/ccpp/driver/GFS_restart.F90 UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90
 UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta
 UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/noahmpdrv.F90 UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/noahmpdrv.meta
 UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90
 UFSATM/ccpp/physics/physics/SFC_Models/SeaIce/CICE/sfc_sice.f UFSATM/ccpp/physics/physics/SFC_Models/SeaIce/CICE/sfc_sice.meta"
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $1/ $2/; }
snap() { for f in $FILES; do mkdir -p $E/stage14/$1/$2/$(dirname $f); cp $E/$1/ufs-weather-model/$f $E/stage14/$1/$2/$f; done; }
pat() { (cd $1 && patch $2 -F0 -s < $3) || { echo "ABORT: $(basename $3) $2 in $1"; exit 1; }; }
d=$E/stage14; rm -rf "${d:?}"
for pr in "full13 full14" "mq13 mq14"; do
  set -- $pr; cp_tree $E/$1 $E/$2; t=$2; W=$E/$t/ufs-weather-model
  snap $t s0
  pat $W "-R -p1" $T8; pat $W/UFSATM/ccpp/physics -p1 $H8
  $P -I $X $W REV $C3 || { echo "ABORT: REV canopy 03 on $t"; exit 1; }
  pat $W/UFSATM/ccpp/physics -p1 $H9
  [ -z "$(grep -rl thompson_sed_actual $W/UFSATM/ccpp)" ] || { echo "ABORT: thompson_sed_actual left in $t: $(grep -rl thompson_sed_actual $W/UFSATM/ccpp)"; exit 1; }
  snap $t s1
  $P -I $X $W PL1 || { echo "ABORT: PL1 on $t"; exit 1; }
  n=$(grep -rl sfc_precip_t1_carry $W/UFSATM/ccpp | grep -v em_p01 | wc -l); [ "$n" = 0 ] || { echo "ABORT: sfc_precip_t1_carry left in $t"; exit 1; }
  snap $t s2
  $P -I $X $W NM10R || { echo "ABORT: NM10R on $t"; exit 1; }
  snap $t s3
  find $W -name "*.orig" -newer $N10 -delete; [ -z "$(find $W/UFSATM -name '*.rej')" ] || { echo "ABORT: rej in $t"; exit 1; }
done
$P -I $X $E/mq14/ufs-weather-model EM01 || { echo "ABORT: EM01"; exit 1; }
$P -I $E/tools/instrument_land14.py $E/mq14/ufs-weather-model || { echo "ABORT: land meter"; exit 1; }
for t in full14 mq14; do for f in $FILES; do cmp -s $E/stage14/$t/s3/$f $E/$t/ufs-weather-model/$f || [ $t = mq14 ] || { echo "ABORT: $t $f changed after s3"; exit 1; }; done; done
# delta diffs (series form) from the full14 stages
cd $E/stage14/full14; for p in "s0 s1 TH8-TH9_unconditional" "s1 s2 PL1_folded_into_EP1" "s2 s3 NM10r"; do set -- $p
  (diff -ruN $1 $2 | sed -e "s|^--- $1/|--- a/|" -e "s|^+++ $2/|+++ b/|" -e "/^diff -ruN/d") > $E/stage14/delta_$3.diff
  echo "delta $3: $(grep -c '^[-+][^-+]' $E/stage14/delta_$3.diff) lines, files: $(lsdiff --strip=1 $E/stage14/delta_$3.diff | sed 's|.*/||' | tr '\n' ' ')"; done
# bug-fix arm
for t in gB14 gB14x; do cp_tree $E/gB13 $E/$t; W=$E/$t/ufs-weather-model
  pat $W "-R -p1" $T8; pat $W/UFSATM/ccpp/physics -p1 $H8; pat $W/UFSATM/ccpp/physics -p1 $H9
  [ $t = gB14 ] && { pat $W -p2 $N10; echo "gB14 NM10r"; }; echo "$t: TH8(held)+TH9"; done
# fx-cut TH8+TH9 diff
M=UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90; R=$E/stage14/fxcut; mkdir -p $R/a/$(dirname $M) $R/b/$(dirname $M)
cp $E/fx/ufs-weather-model/$M $R/a/$M; cp $E/fx/ufs-weather-model/$M $R/b/$M
(cd $R/b/UFSATM/ccpp/physics && patch -p1 -F0 -s < $H8 && patch -p1 -F0 -s < $H9) || { echo "ABORT: fx-cut"; exit 1; }
(cd $R && diff -u a/$M b/$M) > $E/stage14/13_TH8-TH9_unconditional_on_fx.diff
cmp -s $R/b/$M $E/gB14/ufs-weather-model/$M && echo "fx-cut module == gB14 module (gB14 = fx + R1 ... + TH8+TH9)" || echo "NOTE: gB14 module differs from fx+TH8+TH9 (other bug fixes in gB)"
cd $E
sub() { sbatch -J e_$1 --export=NONE,SRC=$E/$1/ufs-weather-model,CLEAN=YES build64.sbatch; }
wait2() { sleep 30; while [ "$(squeue -h -n e_full14,e_mq14,e_gB14,e_gB14x 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done; }
sub full14; sub mq14; wait2; sub gB14; wait2; sub gB14x
echo "TREES SUBMITTED"
