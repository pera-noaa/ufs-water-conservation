#!/bin/bash
# q_ps.sh: progsigma = .true. (operational HAFS v2.1) ensembles, 20 members each: develop (q/devP exe, dbgeta) and the
# 24 fixes (q/t1a exe, dbg4 only).
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp
for pair in devPps:devP t1aps:t1a; do
  IFS=: read n t <<< "$pair"
  for v in $(seq 1000 -1 981); do
    ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
    $H/mkexp_ps.sh q_${n}_c$v $Q/$t/tests/fv3_hafsw_intel.exe "$ed" | tail -1
  done
done
echo "PS LAUNCHED $(date -Is)"
