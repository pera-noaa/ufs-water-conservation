#!/bin/bash
# q_rt2.sh: red-team runs for #401.
#   dose: the convective TKE source scaled by 0.5 (S50) and 0.25 (S25) on develop, 20 members (w_u scaled by sqrt)
#   dt:   develop (devP2's exe) at dt_atmos 180 s, 20 members
#   power: 40 more members (consv_te 0.980 ... 0.941) of t1a and t1aA with their existing executables
# dbg4 + dbgeta2 in the new builds. Base tree q/devA with SAMF restored.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics
mem() { # <tag> <exe> <first v> <last v> [model_configure sed]
  local n=$1 x=$2 v
  [ -f $x ] || { echo "$n: NO EXE $x"; return 1; }
  for v in $(seq $3 -1 $4); do
    local ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
    if [ -n "${5:-}" ]; then $H/mkexp_mc.sh q_${n}_c$v $x "$5" "$ed" | tail -1
    elif [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c$v $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "$ed" | tail -1; fi
  done; }
build() { # <tree> <scale literal for w_u>
  local n=$1 k=$2 T=$Q/$1 d f s j g c
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $Q/devA/ $T/ || return 1
  git -C $T/$PH checkout -q -- physics/CONV/SAMF/samfdeepcnv.f physics/CONV/SAMF/samfshalcnv.f
  [ -z "$(git -C $T/$PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "$n: SAMF not restored"; return 1; }
  d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f
  for g in $f $s; do
    c=$(grep -c '^              ptem = tem / (tem2 \* tem1)$' $g)
    sed -i "s/^              ptem = tem \/ (tem2 \* tem1)\$/&\n              ptem = ptem * $k/" $g
    [ "$(grep -c "^              ptem = ptem \* $k\$" $g)" = "$c" ] && [ $c -ge 1 ] || { echo "$n: scale not applied $g"; return 1; }
  done
  for g in $f $s; do
    [ -z "$(git -C $T/$PH diff -U0 -- ${g#$T/$PH/} | grep '^+[^+]' | cut -c2- | awk 'length($0)>72 && !/^[!cC*]/')" ] || { echo "$n: line past column 72"; return 1; }
  done
  git -C $T/$PH diff -- physics/CONV/SAMF > $Q/rt2_$n.diff
  echo "$n: w_u x $k; SAMF diff deep +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfdeepcnv.f | cut -f1) shal +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfshalcnv.f | cut -f1)"
  awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta2_deep.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; while((getline l < e)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f
  awk -v s=$H/dbg4_shal.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $s > $s.new && mv $s.new $s
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log)"
  mem $n $T/tests/fv3_hafsw_intel.exe 1000 981
}
build devS50 0.70710678_conv_wp > $Q/rt2_devS50.log 2>&1 &
build devS25 0.5_conv_wp > $Q/rt2_devS25.log 2>&1 &
mem t1a $Q/t1a/tests/fv3_hafsw_intel.exe 980 941 > $Q/rt2_t1a.log 2>&1 &
mem t1aA $Q/t1aA/tests/fv3_hafsw_intel.exe 980 941 > $Q/rt2_t1aA.log 2>&1 &
( while [ ! -f $Q/devP2/tests/fv3_hafsw_intel.exe ] || pgrep -f "compile_devP2" >/dev/null || squeue -u $USER -h -o "%.40j" | grep -q "hx_build_qdevP2"; do sleep 60; done
  mem devP2dt180 $Q/devP2/tests/fv3_hafsw_intel.exe 1000 981 "s/^dt_atmos: *90$/dt_atmos:                180/" ) > $Q/rt2_dt180.log 2>&1 &
wait
cat $Q/rt2_*.log | grep -v "^q_"
echo "RT2 LAUNCHED $(date -Is)"
