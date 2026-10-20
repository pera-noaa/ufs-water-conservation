#!/bin/bash
# q_ens3.sh: (1) split sea ice/NSST inside 1a: t1ar = 1a minus the NSST rain fix, t1ai = 1a minus the three sea-ice fixes
# (10 members each); (2) 10 more members (consv_te 0.990 ... 0.981) for dev, t1a, t1ans
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics; FV=UFSATM/fv3/atmos_cubed_sphere
members() { # <tree> <from v> <to v> (v=1000 means consv_te 1)
  local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  [ -f $x ] || { echo "$n: NO EXE"; return 1; }
  for v in $(seq $2 -1 $3); do
    if [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c1000 $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done
}
build() { # <tree> <files wanted> <commits to revert, newest first...> : 1a merged, then the reverts
  local n=$1 want=$2; shift 2; local T=$Q/$n pin d j b c
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/ufs-weather-model/ $T/ || return 1
  for r in $PH $FV UFSATM NOAHMP-interface/noahmp; do
    git -C $T/$r fetch -q --no-recurse-submodules $S/$r "+refs/heads/pr1-*:refs/heads/pr1-*" || { echo "$n: fetch fail $r"; return 1; }
  done
  git -C $T/UFSATM checkout -q pr1-round1 && git -C $T/NOAHMP-interface/noahmp checkout -q pr1-round1 || { echo "$n: checkout fail"; return 1; }
  for b in pr1-samf pr1-noahmp pr1-seaice_nsst pr1-gfdlmp; do
    git -C $T/$PH -c user.name=attr -c user.email=attr@localhost merge -q --no-edit $b >/dev/null 2>&1 || { echo "$n: MERGE CONFLICT $b"; return 1; }
  done
  for c in "$@"; do
    git -C $T/$PH -c user.name=attr -c user.email=attr@localhost revert --no-edit $c >/dev/null 2>&1 || { echo "$n: revert fail ${c:0:8}"; return 1; }
  done
  pin=$(git -C $P/ufs-weather-model/$PH rev-parse HEAD)
  [ "$(git -C $T/$PH diff --name-only $pin HEAD | wc -l)" = $want ] || { echo "$n: ccpp files vs pin $(git -C $T/$PH diff --name-only $pin HEAD | wc -l) != $want"; return 1; }
  [ "$(git -C $T/$FV rev-parse HEAD)" = "$(git -C $P/ufs-weather-model/$FV rev-parse HEAD)" ] || { echo "$n: fv3 not at develop"; return 1; }
  d=$T/$PH/physics/CONV/SAMF
  echo "$n: physics $(git -C $T/$PH rev-parse --short HEAD); files $want; nst $(git -C $T/$PH diff --name-only $pin HEAD | grep -c sfc_nst) sice $(git -C $T/$PH diff --name-only $pin HEAD | grep -c sfc_sice) PBL05 $(git -C $T/$PH diff --name-only $pin HEAD | grep -c satmedmfvdifq)"
  for x in deep:samfdeepcnv shal:samfshalcnv; do f=$d/${x#*:}.f
    awk -v s=$H/dbg4_${x%%:*}.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f; done
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $T/tests/fv3_hafsw_intel.exe 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL')"
  members $n 1000 991
}
for n in dev t1a t1ans; do members $n 990 981; done
build t1ar 15 66535600b01964e8f01ba11c46faf3d23e2842e7 > $Q/ens_t1ar.log 2>&1 &
build t1ai 14 b36e746343ac0729b3de157f5c8b19ab98f7c65a 282e2cdcec74d51e9b91b09711a2f7552a4042ef b6b9565f8d0e2676e68af81b7c7137c5e641090e > $Q/ens_t1ai.log 2>&1 &
wait
cat $Q/ens_t1ar.log $Q/ens_t1ai.log
echo "ENS3 LAUNCHED $(date -Is)"
