#!/bin/bash
# q_han.sh: the #401 reply tests, on develop and on the 24-fix set (t1a), 20 members each (consv_te 1 ... 0.981):
#   C  Han's test: eta <= 1 below cloud base and etad <= 1 (capped inside the recursions)
#   T  no convective TKE source ("include TKE contribution from deep/shallow convection" skipped)
#   P  develop unchanged
# Every build carries the print-only dbg4 and dbgeta blocks. Base trees are q/devA and q/t1aA with SAMF restored.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics
members() { local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  [ -f $x ] || { echo "$n: NO EXE"; return 1; }
  for v in $(seq 1000 -1 981); do
    if [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c1000 $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done; }
build() { # <tree> <base devA|t1aA> <option C|T|P>
  local n=$1 src=$Q/$2 opt=$3 T=$Q/$1 d f s j
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $src/ $T/ || return 1
  git -C $T/$PH checkout -q -- physics/CONV/SAMF/samfdeepcnv.f physics/CONV/SAMF/samfshalcnv.f
  [ -z "$(git -C $T/$PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "$n: SAMF not restored"; return 1; }
  [ "$(git -C $T/$PH rev-parse HEAD)" = "$(git -C $src/$PH rev-parse HEAD)" ] || { echo "$n: physics head"; return 1; }
  d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f
  case $opt in
    C) [ "$(grep -c '^              eta(i,k) = eta(i,k+1) / (1.0_conv_wp + ptem \* dz)$' $f)" = 1 ] &&
       [ "$(grep -c '^              etad(i,k) = etad(i,k+1) \* (1.0_conv_wp - ptem \* dz)$' $f)" = 2 ] || { echo "$n: anchor C"; return 1; }
       sed -i -e 's/^              eta(i,k) = eta(i,k+1) \/ (1.0_conv_wp + ptem \* dz)$/              eta(i,k) = min(eta(i,k+1) \/ (1.0_conv_wp + ptem * dz),\n     \&                       1.0_conv_wp)/' \
              -e 's/^              etad(i,k) = etad(i,k+1) \* (1.0_conv_wp - ptem \* dz)$/              etad(i,k) = min(etad(i,k+1) * (1.0_conv_wp - ptem * dz),\n     \&                        1.0_conv_wp)/' $f
       [ "$(grep -c '^     &  *1.0_conv_wp)$' $f)" = 3 ] || { echo "$n: C not applied"; return 1; };;
    T) for g in $f $s; do
         awk '/include TKE contribution from (deep|shallow) convection/{t=1} t==1 && /^      if \(ntk > 0\) then$/{print "      if (ntk > 0 .and. .false.) then"; t=2; next} {print}' $g > $g.new && mv $g.new $g
         [ "$(grep -c 'ntk > 0 .and. .false.' $g)" = 1 ] || { echo "$n: T not applied $g"; return 1; }
       done;;
    P) ;;
  esac
  echo "$n: base $2 option $opt; physics $(git -C $T/$PH rev-parse --short HEAD); SAMF diff deep +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfdeepcnv.f | cut -f1) shal +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfshalcnv.f | cut -f1)"
  awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta_deep.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; while((getline l < e)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f
  awk -v s=$H/dbg4_shal.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $s > $s.new && mv $s.new $s
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $T/tests/fv3_hafsw_intel.exe 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL\|DBGETA')"
  members $n
}
for spec in devC:devA:C t1aC:t1aA:C devT:devA:T t1aT:t1aA:T devP:devA:P; do
  IFS=: read n b o <<< "$spec"; build $n $b $o > $Q/han_$n.log 2>&1 &
done
wait
cat $Q/han_*.log | grep -v "^q_"
echo "HAN LAUNCHED $(date -Is)"
