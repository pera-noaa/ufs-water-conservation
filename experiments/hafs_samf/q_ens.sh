#!/bin/bash
# q_ens.sh: HAFS crash-rate ensembles, 10 members (consv_te 1, 0.999 ... 0.991) per tree.
# Existing trees dev, r37, t1a get members 0.997-0.991; new trees t1anp (1a minus PBL05), t1ans (1a minus sea ice/NSST),
# t1ac (1a + FV3) are built like q_t1a.sh (print-only dbg4 in SAMF) and get all 10.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics; FV=UFSATM/fv3/atmos_cubed_sphere
members() { # <tree> <first v> : launch members c<v>..c991 (v=1000 means consv_te 1)
  local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  [ -f $x ] || { echo "$n: NO EXE"; return 1; }
  for v in $(seq $2 -1 991); do
    if [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c1000 $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done
}
build() { # <tree> : make, instrument, compile, launch 10 members
  local n=$1 T=$Q/$1 pin d j b
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/ufs-weather-model/ $T/ || return 1
  for r in $PH $FV UFSATM NOAHMP-interface/noahmp; do
    git -C $T/$r fetch -q --no-recurse-submodules $S/$r "+refs/heads/pr1-*:refs/heads/pr1-*" || { echo "$n: fetch fail $r"; return 1; }
  done
  git -C $T/UFSATM checkout -q pr1-round1 && git -C $T/NOAHMP-interface/noahmp checkout -q pr1-round1 || { echo "$n: checkout fail"; return 1; }
  local br="pr1-samf pr1-noahmp pr1-seaice_nsst pr1-gfdlmp" want=16
  [ $n = t1ans ] && { br="pr1-samf pr1-noahmp pr1-gfdlmp"; want=13; }
  for b in $br; do
    git -C $T/$PH -c user.name=attr -c user.email=attr@localhost merge -q --no-edit $b >/dev/null 2>&1 || { echo "$n: MERGE CONFLICT $b"; return 1; }
  done
  if [ $n = t1anp ]; then
    git -C $T/$PH -c user.name=attr -c user.email=attr@localhost revert -q --no-edit 5c20e35ab3f5fd9e1b5c088d86c4a41906c45fdc >/dev/null 2>&1 || { echo "$n: revert fail"; return 1; }
    want=15
  fi
  [ $n = t1ac ] && { git -C $T/$FV checkout -q pr1-round1 || { echo "$n: fv3 checkout fail"; return 1; }; }
  pin=$(git -C $P/ufs-weather-model/$PH rev-parse HEAD)
  [ "$(git -C $T/$PH diff --name-only $pin HEAD | wc -l)" = $want ] || { echo "$n: ccpp files vs pin != $want"; return 1; }
  local fvwant=$(git -C $P/ufs-weather-model/$FV rev-parse HEAD); [ $n = t1ac ] && fvwant=$(git -C $S/$FV rev-parse pr1-round1)
  [ "$(git -C $T/$FV rev-parse HEAD)" = "$fvwant" ] || { echo "$n: fv3 head wrong"; return 1; }
  d=$T/$PH/physics/CONV/SAMF
  echo "$n: physics $(git -C $T/$PH rev-parse --short HEAD) fv3 $(git -C $T/$FV rev-parse --short HEAD) ufsatm $(git -C $T/UFSATM rev-parse --short HEAD); files $want; PBL05 $(git -C $T/$PH diff --name-only $pin HEAD | grep -c satmedmfvdifq) sice $(git -C $T/$PH diff --name-only $pin HEAD | grep -c sfc_sice)"
  for x in deep:samfdeepcnv shal:samfshalcnv; do f=$d/${x#*:}.f
    awk -v s=$H/dbg4_${x%%:*}.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f; done
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $T/tests/fv3_hafsw_intel.exe 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL')"
  members $n 1000
}
for n in dev r37 t1a; do members $n 997; done
for n in t1anp t1ans t1ac; do build $n > $Q/ens_$n.log 2>&1 & done
wait
cat $Q/ens_t1anp.log $Q/ens_t1ans.log $Q/ens_t1ac.log
echo "ENS LAUNCHED $(date -Is)"
