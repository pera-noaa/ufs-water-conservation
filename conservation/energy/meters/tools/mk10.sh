#!/bin/bash
# usage: nohup mk10.sh & : full10/mq10 = full9/mq9 with trdyn 01_DYN v5 replaced by 04_INLQ + v6. 04 and v5->v6 touch
# only sw_core.F90 (v6 = v5 rebased on 04: trw_d uses dpm), so sw_core = <tree>6 + 04 + v6, after checking that
# <tree>9's sw_core = <tree>6 + v5 (nothing else edits it); build both
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn/patches
I4=$E/accepted/18c_trdyn_04_INLQ_inline_q_damping_mass_single_valued.diff; V6=$E/accepted/18d_trdyn_01_DYN_dry_tracer_adv_remap_ic_v6.diff
V5=$E/accepted/18b_trdyn_01_DYN_dry_tracer_adv_remap_ic_v5.diff
cp -p $T/04_INLQ_inline_q_damping_mass_single_valued.diff $I4; cp -p $T/01_DYN_dry_tracer_adv_remap_ic_v6.diff $V6
SW=UFSATM/fv3/atmos_cubed_sphere/model/sw_core.F90
body() { filterdiff -x "*sw_core.F90" "$1" | grep "^[-+]" | grep -v "^+++\|^---"; }
[ "$(lsdiff --strip=1 $V6 | md5sum)" = "$(lsdiff --strip=1 $V5 | md5sum)" ] && [ "$(body $V6 | md5sum)" = "$(body $V5 | md5sum)" ] \
  || { echo "ABORT: v6 differs from v5 outside sw_core"; exit 1; }
for pr in "full6 full9 full10" "mq6 mq9 mq10"; do
  set -- $pr; S=$E/$2; D=$E/$3; R=$E/scratch_v6ref_$3
  rm -rf "${R:?}"; mkdir -p $R/a/$(dirname $SW) $R/b/$(dirname $SW)
  cp $E/$1/ufs-weather-model/$SW $R/a/$SW; cp $E/$1/ufs-weather-model/$SW $R/b/$SW
  (cd $R/a && filterdiff -i "*sw_core.F90" $V5 | patch -p1 -F0 -s) || { echo "ABORT: v5 ref $1"; exit 1; }
  cmp -s $R/a/$SW $S/ufs-weather-model/$SW && echo "$2 sw_core == $1 + v5" || { echo "ABORT: $2 sw_core != $1 + v5"; exit 1; }
  (cd $R/b && patch -p1 -F0 -s < $I4 && filterdiff -i "*sw_core.F90" $V6 | patch -p1 -F0 -s) || { echo "ABORT: 04+v6 on $1"; exit 1; }
  [ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
  rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
  cp $R/b/$SW $D/ufs-weather-model/$SW; echo "$3 sw_core = $1 + 04 + v6 ($(diff $S/ufs-weather-model/$SW $D/ufs-weather-model/$SW | grep -c '^[<>]') lines vs $2)"
  rm -rf "${R:?}"
done
cd $E
while squeue -h -j 10154961,10154962 2>/dev/null | grep -q .; do sleep 60; done  # <= 2 own jobs
sbatch -J e_mq10 --export=NONE,SRC=$E/mq10/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_full10 --export=NONE,SRC=$E/full10/ufs-weather-model,CLEAN=YES build64.sbatch
