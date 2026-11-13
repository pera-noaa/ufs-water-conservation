#!/bin/bash
# q_fix.sh: candidate fixes for #401 on develop and on the 24-fix set (t1a), 20 members each, 6 h:
#   A  the issue's option A: xmb bounded by dp/(g dt2 eta) from kb to ktcon (optD.f)
#   F  entrainment floor scaled with clamt: crtlame * max(1, clamt/clam)
#   G  the convective TKE source's w_u bounded by the scheme's updraft velocity wc (deep updraft, downdraft, shallow)
#   H  the convective TKE source as a level: tke = max(tke, 0.5 sigma w_u^2), not an increment per call
#   P2 develop unchanged
# Every build carries dbg4 and dbgeta2 (print only). Then 48 h runs, 10 members, of P2 and A.
# Base trees are q/devA and q/t1aA with SAMF restored.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics
members() { local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  [ -f $x ] || { echo "$n: NO EXE"; return 1; }
  for v in $(seq 1000 -1 981); do
    if [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c1000 $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done; }
long() { local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  for v in $(seq 1000 -1 991); do
    if [ $v = 1000 ]; then $H/mkexp_long.sh q_${n}_L1000 $x 48 | tail -1
    else $H/mkexp_long.sh q_${n}_L$v $x 48 "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done; }
build() { # <tree> <base devA|t1aA> <option A|F|G|H|P>
  local n=$1 src=$Q/$2 opt=$3 T=$Q/$1 d f s j c
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $src/ $T/ || return 1
  git -C $T/$PH checkout -q -- physics/CONV/SAMF/samfdeepcnv.f physics/CONV/SAMF/samfshalcnv.f
  [ -z "$(git -C $T/$PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "$n: SAMF not restored"; return 1; }
  [ "$(git -C $T/$PH rev-parse HEAD)" = "$(git -C $src/$PH rev-parse HEAD)" ] || { echo "$n: physics head"; return 1; }
  d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f
  case $opt in
    A) [ "$(grep -c 'xmbmax(i) = dp / (real(grav, kind=conv_wp)' $f)" = 1 ] || { echo "$n: anchor A"; return 1; }
       awk -v s=$H/optD.f '{print} /xmbmax\(i\) = dp \/ \(real\(grav, kind=conv_wp\)/{g=1} g==1 && /^      enddo/{while((getline l < s)>0) print l; g=2}' $f > $f.new && mv $f.new $f;;
    F) c='^            xlamue(i,k) = max(xlamue(i,k), crtlame)$'
       [ "$(grep -c "$c" $f)" = 1 ] || { echo "$n: anchor F"; return 1; }
       sed -i "s/$c/            xlamue(i,k) = max(xlamue(i,k), crtlame *\n     \&        max(1.0_conv_wp, clamt(i) \/ real(clam, kind=conv_wp)))/" $f;;
    G) for g in $f $s; do
         c=$(grep -c '^              ptem = tem / (tem2 \* tem1)$' $g)
         sed -i 's/^              ptem = tem \/ (tem2 \* tem1)$/&\n              ptem = min(ptem, wc(i))/' $g
         [ "$(grep -c '^              ptem = min(ptem, wc(i))$' $g)" = "$c" ] && [ $c -ge 1 ] || { echo "$n: G not applied $g"; return 1; }
       done;;
    H) for g in $f $s; do
         c=$(grep -c 'new_qtr(i,k,ntk) = new_qtr(i,k,ntk) + 0.5_conv_wp \* tem2$' $g)
         awk '/^              new_qtr\(i,k,ntk\) = new_qtr\(i,k,ntk\) \+ 0\.5_conv_wp \* tem2$/{print "              new_qtr(i,k,ntk) = max(new_qtr(i,k,ntk),"; h=1; next}
              h==1 && /^     &  *\* ptem \* ptem$/{print "     &                         0.5_conv_wp * tem2 * ptem * ptem)"; h=0; next} {h=0; print}' $g > $g.new && mv $g.new $g
         [ "$(grep -c '^              new_qtr(i,k,ntk) = max(new_qtr(i,k,ntk),$' $g)" = "$c" ] &&
         [ "$(grep -c '^     &  *0.5_conv_wp \* tem2 \* ptem \* ptem)$' $g)" = "$c" ] && [ $c -ge 1 ] || { echo "$n: H not applied $g"; return 1; }
       done;;
    P) ;;
  esac
  for g in $f $s; do  # fixed form: no changed code line past column 72
    [ -z "$(git -C $T/$PH diff -U0 -- ${g#$T/$PH/} | grep '^+[^+]' | cut -c2- | awk 'length($0)>72 && !/^[!cC*]/')" ] || { echo "$n: line past column 72 in $g"; return 1; }
  done
  echo "$n: base $2 option $opt; physics $(git -C $T/$PH rev-parse --short HEAD); SAMF diff deep +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfdeepcnv.f | cut -f1) shal +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfshalcnv.f | cut -f1)"
  git -C $T/$PH diff -- physics/CONV/SAMF > $Q/fix_$n.diff
  awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta2_deep.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; while((getline l < e)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f
  awk -v s=$H/dbg4_shal.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $s > $s.new && mv $s.new $s
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $T/tests/fv3_hafsw_intel.exe 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL\|DBGETA')"
  members $n
  case $n in devP2|devA2) long $n;; esac
}
for spec in devP2:devA:P devA2:devA:A t1aA2:t1aA:A devF:devA:F t1aF:t1aA:F devG:devA:G t1aG:t1aA:G devH:devA:H t1aH:t1aA:H; do
  IFS=: read n b o <<< "$spec"; build $n $b $o > $Q/fix_$n.log 2>&1 &
done
wait
cat $Q/fix_*.log | grep -v "^q_"
echo "FIX LAUNCHED $(date -Is)"
