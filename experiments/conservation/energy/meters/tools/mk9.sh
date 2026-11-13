#!/bin/bash
# usage: nohup mk9.sh & : full9/mq9 = full6/mq6 + trdyn 02b 03b 01_DYN_v5 (-F0, clashes re-anchored by rebase_trdyn.py)
# + ensfc2 04 05 06 08 09 10 11 (-p2 -F0; not 12); mq9 probes regenerated (EB_PBLFLX=1 EB_PH1=1); build both
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
P2=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/patches; V5=$E/accepted/18b_trdyn_01_DYN_dry_tracer_adv_remap_ic_v5.diff
for pr in "full6 full9" "mq6 mq9"; do
  set -- $pr; S=$E/$1; D=$E/$2
  [ -e "$D" ] && { echo "ABORT: $D exists"; exit 1; }
  rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $S/ $D/
  cd $D/ufs-weather-model/UFSATM/ccpp/physics
  patch -p1 -F0 < $E/accepted/16_trdyn_02b_T1_samf_tracer_substep.diff | grep -i -E "FAILED|reject" || true
  patch -p1 -F0 < $E/accepted/17_trdyn_03b_DRY_chem_tracers_dry_mixing_ratio_transport.diff | grep -i -E "FAILED|reject" || true
  cd $D/ufs-weather-model
  patch -p1 -F0 < $V5 | grep -i -E "FAILED|reject" || true
  $P -I $E/tools/rebase_trdyn.py $D/ufs-weather-model || { echo "ABORT: rejects left on $D"; exit 1; }
  [ -z "$(find $D/ufs-weather-model -name '*.rej')" ] || { echo "ABORT: .rej left on $D"; exit 1; }
  find $D/ufs-weather-model -name "*.orig" -newer $V5 -delete
  for f in 04_sfc_SI1 05_sfc_SI2 06_sfc_NP1 08_sfc_QR1 09_sfc_CMC 10_sfc_FL1 11_sfc_options; do
    patch -p2 -F0 -s < $P2/$f.diff || { echo "ABORT: $f on $D"; exit 1; }
    echo "$D $f $(md5sum < $P2/$f.diff | cut -c1-12)"
  done
done
EB_PBLFLX=1 EB_PH1=1 $P -I $E/tools/instrument_eb_phys2.py $E/mq9/ufs-weather-model
cd $E
sbatch -J e_mq9 --export=NONE,SRC=$E/mq9/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_full9 --export=NONE,SRC=$E/full9/ufs-weather-model,CLEAN=YES build64.sbatch
