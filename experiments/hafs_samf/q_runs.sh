#!/bin/bash
# launch 3 members (consv_te 1, 0.999, 0.998) for each q/ tree as its build finishes
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp
left="dev fv3 fv3samf fv3sice phys full fullT1"
while [ -n "$left" ]; do
  next=""
  for n in $left; do
    if squeue -u $USER -h -n hx_build_q$n -o %i | grep -q .; then next="$next $n"; continue; fi
    x=$Q/$n/tests/fv3_hafsw_intel.exe
    if [ ! -f $x ]; then echo "$n: NO EXE ($(grep -h BUILD_RC $Q/compile_$n.*.log | tail -1))"; continue; fi
    echo "$n: $(grep -h BUILD_RC $Q/compile_$n.*.log | tail -1); dbg strings $(strings $x | grep -c 'DBGSAMF\|DBGSHAL')"
    $H/mkexp.sh q_${n}_c1000 $x | tail -1
    for v in 999 998; do $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; done
  done
  left=$(echo $next); [ -n "$left" ] && sleep 60
done
echo "ALL LAUNCHED $(date -Is)"
