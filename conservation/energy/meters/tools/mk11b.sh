#!/bin/bash
# usage: nohup mk11b.sh & : integrator fix for ensfc2 16 (GFS_MP_generic_post.meta [tgrs] standard_name air_temperature, the
# name of gt0 here -> capgen duplicate; PH1 wants the step-start T1 = physics_timestep_initial_air_temperature) in full11
# and mq11; gB11 = gB + ensfc2 13 14 15 (TH9 is switch-gated and cut on K1/TFH text: not applicable to fx). Builds.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; A=$E/accepted
for t in full11 mq11; do
  m=$E/$t/ufs-weather-model/UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta
  n=$(grep -n -A1 "^\[tgrs\]" $m | grep -c "standard_name = air_temperature$"); [ "$n" = 1 ] || { echo "ABORT: $t meta anchor $n"; exit 1; }
  l=$(( $(grep -n "^\[tgrs\]" $m | cut -d: -f1) + 1 ))
  sed -i "${l}s/standard_name = air_temperature$/standard_name = physics_timestep_initial_air_temperature/" $m
  echo "$t: $(sed -n "$((l-1)),${l}p" $m | tr '\n' ' ')"
done
d=$E/gB11; rm -rf "${d:?}"
rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $E/gB/ $E/gB11/
for f in 24_ensfc2_13_sfc_SL2 25_ensfc2_14_sfc_CS1 26_ensfc2_15_sfc_CB1; do
  (cd $E/gB11/ufs-weather-model && patch -p2 -F0 -s < $A/$f.diff) || { echo "ABORT: $f on gB11"; exit 1; }; echo "gB11 $f"; done
cd $E
sbatch -J e_full11 --export=NONE,SRC=$E/full11/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_mq11 --export=NONE,SRC=$E/mq11/ufs-weather-model,CLEAN=YES build64.sbatch
sleep 30; while [ "$(squeue -h -n e_full11,e_mq11 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done
sbatch -J e_gB11 --export=NONE,SRC=$E/gB11/ufs-weather-model,CLEAN=YES build64.sbatch
echo "TREES SUBMITTED"
