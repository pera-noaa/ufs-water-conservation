#!/bin/bash
# q_psF.sh: the floor (F, q/devF exe: dbg4 + dbgeta2) with progsigma = .true. (operational HAFS v2.1):
# 20 members x 6 h and 10 members x 48 h, as develop's progsigma sets (q_ps.sh, mkexp_psl.sh).
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp; x=$Q/devF/tests/fv3_hafsw_intel.exe
[ -f $x ] || { echo "NO EXE $x"; exit 1; }
for v in $(seq 1000 -1 981); do ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
  $H/mkexp_ps.sh q_devFps_c$v $x "$ed" | tail -1; done
for v in $(seq 1000 -1 991); do ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
  $H/mkexp_psl.sh q_devFps_L$v $x 48 "$ed" | tail -1; done
echo "PSF LAUNCHED $(date -Is)"
