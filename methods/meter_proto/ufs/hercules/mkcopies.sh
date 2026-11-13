#!/bin/bash
set -e
M=/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto; S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/rt_sxd5
for d in src_fix src_dev; do
  rsync -a --exclude='/tests/*.exe' --exclude='/tests/build_*' --exclude='/tests/logs/log_*' --exclude='/tests/run_dir' --exclude='/build/' --exclude='/tests/modules.fv3_*' $S/ $M/$d/
  echo "$d copied $(date -Is)"
done
cd $M/src_dev/UFSATM/ccpp/physics && git checkout -q b7cb19b1266a8d325d5313507917e2a6c9992230 && git log --oneline -1
cd $M/src_fix/UFSATM/ccpp/physics && git diff b7cb19b1266a8d325d5313507917e2a6c9992230 44defba356ed0e677c02829b8e94887308fe6630 > $M/pkg1_physics.diff && git diff --stat b7cb19b1266a8d325d5313507917e2a6c9992230 44defba356ed0e677c02829b8e94887308fe6630 | tail -3
echo COPIES_DONE
