#!/bin/bash
# q_w.sh NAME GATE PATCH...: q_sa1.sh's build (devA with SAMF restored + PATCHes + dbg4/dbgeta2/dbg4_shal) plus the
# print-only SA1 water counter (dbgw_*.f: DBGWD/DBGWS lines); hafs_global_1nest_atm 2 x 6 h, 1 x 48 h, 1 x 48 h progsigma.
# Settles whether SA1's HAFS precipitation drop is the water it stops creating.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp; PH=UFSATM/ccpp/physics; n=$1; g=$2; shift 2; T=$Q/$n
[ -e $T ] && { echo "$n exists"; exit 1; }
rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $Q/devA/ $T/ || exit 1
git -C $T/$PH checkout -q -- physics/CONV/SAMF/samfdeepcnv.f physics/CONV/SAMF/samfshalcnv.f
[ -z "$(git -C $T/$PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "SAMF not restored"; exit 1; }
for p; do git -C $T/$PH apply $H/$p || { echo "patch $p"; exit 1; }; done
[ "$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF | awk '{a+=$1; d+=$2} END {print a" "d}')" = "$g" ] || { echo "diff size"; exit 1; }
git -C $T/$PH diff -- physics/CONV/SAMF > $Q/w_$n.diff
d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f; cp $f $Q/w_$n.deep0; cp $s $Q/w_$n.shal0
for a in "delqbar(im), delqev(im), deltbar(im)," "      flxtvd = 0.0_conv_wp" "! subtract the double counting change rates at jmin+1 & kb beforehand" "!> - Calculate convective cloud water."; do
  [ "$(grep -cF -- "$a" $f)" -ge 1 ] || { echo "deep anchor: $a"; exit 1; }; done
[ "$(grep -cxF '              flxtvd(i,k) = eta(i,k) * tem1' $s)" = 1 ] && [ "$(grep -cxF 'c      convective cloud water' $s)" = 1 ] || { echo "shal anchor"; exit 1; }
awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta2_deep.f -v a=$H/dbgw_deepacc.f -v p=$H/dbgw_printD.f '
  !dl && index($0, "delqbar(im), delqev(im), deltbar(im),") {print; print "     &                     dbgwq(im),"; dl=1; next}
  !fi && $0 == "      flxtvd = 0.0_conv_wp" {print "      dbgwq = 0.0_conv_wp"; fi=1}
  !pr && $0 == "!> - Calculate convective cloud water." {while((getline l < p)>0) print l; pr=1}
  !ng && /^! Negative moisture is set to zero after borrowing/ {while((getline l < s)>0) print l; while((getline l < e)>0) print l; ng=1}
  {print}
  !ac && $0 == "! subtract the double counting change rates at jmin+1 & kb beforehand" {while((getline l < a)>0) print l; ac=1}' $f > $f.new && mv $f.new $f
awk -v s=$H/dbg4_shal.f -v a=$H/dbgw_shalacc.f -v p=$H/dbgw_printS.f '
  !dl && index($0, "delqbar(im), delqev(im), deltbar(im),") {print; print "     &                     dbgwq(im),"; dl=1; next}
  !fi && $0 == "      flxtvd = 0.0_conv_wp" {print "      dbgwq = 0.0_conv_wp"; fi=1}
  !pr && $0 == "c      convective cloud water" {while((getline l < p)>0) print l; pr=1}
  !ng && /^! Negative moisture is set to zero after borrowing/ {while((getline l < s)>0) print l; ng=1}
  {print}
  !ac && $0 == "              flxtvd(i,k) = eta(i,k) * tem1" {while((getline l < a)>0) print l; ac=1}' $s > $s.new && mv $s.new $s
# print-only gate: only added lines
ed=$(( $(cat $H/dbg4_deep.f $H/dbgeta2_deep.f $H/dbgw_deepacc.f $H/dbgw_printD.f | wc -l) + 1 )); es=$(( $(cat $H/dbg4_shal.f $H/dbgw_shalacc.f $H/dbgw_printS.f | wc -l) + 1 ))
gd="$(diff $Q/w_$n.deep0 $f | grep -c '^>') $(diff $Q/w_$n.deep0 $f | grep -c '^<')"; gs="$(diff $Q/w_$n.shal0 $s | grep -c '^>') $(diff $Q/w_$n.shal0 $s | grep -c '^<')"
[ "$gd" = "$((ed+1)) 0" ] && [ "$gs" = "$((es+1)) 0" ] || { echo "dbg gate: deep $gd (want $((ed+1)) 0) shal $gs (want $((es+1)) 0)"; exit 1; }
# fixed form: no code line past column 72 that the original did not have (10-22: a 73-column declaration broke the build)
for x in "$f $Q/w_$n.deep0" "$s $Q/w_$n.shal0"; do set -- $x
  [ "$(awk '!/^[!cC*]/ && length > 72' $1 | wc -l)" = "$(awk '!/^[!cC*]/ && length > 72' $2 | wc -l)" ] || { echo "column-72 gate: $1"; exit 1; }; done
sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
x=$T/tests/fv3_hafsw_intel.exe
echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $x 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL\|DBGETA\|DBGWD\|DBGWS')"
[ -f $x ] || { echo "NO EXE"; exit 1; }
for v in 1000 999; do ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
  $H/mkexp.sh q_${n}_c$v $x "" "$ed" | tail -1; done
$H/mkexp_long.sh q_${n}_L1000 $x 48 "" | tail -1
$H/mkexp_psl.sh q_${n}ps_L1000 $x 48 "" | tail -1
echo "W LAUNCHED $n $(date -Is)"
