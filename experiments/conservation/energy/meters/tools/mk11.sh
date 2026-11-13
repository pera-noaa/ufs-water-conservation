#!/bin/bash
# usage: nohup mk11.sh & : full11/mq11 = full10/mq10 + ensfc2 r4 (13 SL2, 14 CS1, 15 CB1, 16 options_r4; -p2 -F0) + canopy
# (01 E2, 03 TH9, 04 E1; -p1 -F0); clashes re-anchored by rebase_r11.py (stages 13, E2, TH9, each right after its patch);
# mq11 probes regenerated with the lag meter (EB_PBLFLX EB_PH1 EB_LAG). gB11 = gB (fx + bug fixes) + 13 14 15 + TH9
# (TH8 only with TH9). All three -no-fma.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons; A=$E/accepted; NF=$U/ensfc2/tools/nofma.py
cp -p $U/ensfc2/patches/13_sfc_SL2.diff $A/24_ensfc2_13_sfc_SL2.diff; cp -p $U/ensfc2/patches/14_sfc_CS1.diff $A/25_ensfc2_14_sfc_CS1.diff
cp -p $U/ensfc2/patches/15_sfc_CB1.diff $A/26_ensfc2_15_sfc_CB1.diff; cp -p $U/ensfc2/patches/16_sfc_options_r4.diff $A/27_ensfc2_16_sfc_options_r4.diff
cp -p $U/canopy/patches/01_E2_noahmp_fwet_opt.diff $A/28_canopy_01_E2_noahmp_fwet_opt.diff
cp -p $U/canopy/patches/03_TH9_thompson_sed_actual.diff $A/29_canopy_03_TH9_thompson_sed_actual.diff
cp -p $U/canopy/patches/04_E1_nst_spray_implicit.diff $A/30_canopy_04_E1_nst_spray_implicit.diff
cmp -s $U/canopy/patches/02_TH8_thompson_count_all_sedimented_precip.diff $A/23_energy_06_TH8_thompson_count_all_sedimented_precip.diff && echo "canopy 02 == TH8"
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $1/ $2/; }
pp() {  # pp <tree> <level> <diff> [stage] : -F0; rejects only where a rebase_r11.py stage re-anchors them
  (cd $E/$1/ufs-weather-model && patch -p$2 -F0 < $3 | grep -E "FAILED" ; true); echo "$1 $(basename $3) md5 $(md5sum < $3 | cut -c1-12)"
  if [ -n "${4:-}" ]; then $P -I $E/tools/rebase_r11.py $E/$1/ufs-weather-model $4 || { echo "ABORT: $4 on $1"; exit 1; }
  else [ -z "$(find $E/$1/ufs-weather-model -name '*.rej')" ] || { echo "ABORT: rejects after $(basename $3) on $1"; exit 1; }; fi; }
for pr in "full10 full11" "mq10 mq11"; do
  set -- $pr; cp_tree $E/$1 $E/$2; t=$2
  pp $t 2 $A/24_ensfc2_13_sfc_SL2.diff 13
  for f in 25_ensfc2_14_sfc_CS1 26_ensfc2_15_sfc_CB1 27_ensfc2_16_sfc_options_r4; do pp $t 2 $A/$f.diff; done
  pp $t 1 $A/28_canopy_01_E2_noahmp_fwet_opt.diff E2
  pp $t 1 $A/29_canopy_03_TH9_thompson_sed_actual.diff TH9
  pp $t 1 $A/30_canopy_04_E1_nst_spray_implicit.diff
  find $E/$t/ufs-weather-model -name "*.orig" -newer $A/30_canopy_04_E1_nst_spray_implicit.diff -delete
  $P -I $NF $E/$t/ufs-weather-model
done
EB_PBLFLX=1 EB_PH1=1 EB_LAG=1 $P -I $E/tools/instrument_eb_phys2.py $E/mq11/ufs-weather-model || { echo "ABORT: meter"; exit 1; }
cp_tree $E/gB $E/gB11
for f in 24_ensfc2_13_sfc_SL2 25_ensfc2_14_sfc_CS1 26_ensfc2_15_sfc_CB1; do
  (cd $E/gB11/ufs-weather-model && patch -p2 -F0 -s < $A/$f.diff) || { echo "ABORT: $f on gB11"; exit 1; }; echo "gB11 $f"; done
(cd $E/gB11/ufs-weather-model && patch -p1 -F0 -s < $A/29_canopy_03_TH9_thompson_sed_actual.diff) || { echo "ABORT: TH9 on gB11"; exit 1; }; echo "gB11 TH9"
grep -c "no-fma" $E/gB11/ufs-weather-model/cmake/IntelMixed.cmake
cd $E
sbatch -J e_full11 --export=NONE,SRC=$E/full11/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_mq11 --export=NONE,SRC=$E/mq11/ufs-weather-model,CLEAN=YES build64.sbatch
sleep 30; while [ "$(squeue -h -n e_full11,e_mq11 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done
sbatch -J e_gB11 --export=NONE,SRC=$E/gB11/ufs-weather-model,CLEAN=YES build64.sbatch
echo "TREES SUBMITTED"
