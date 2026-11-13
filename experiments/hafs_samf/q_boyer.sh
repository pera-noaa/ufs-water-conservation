#!/bin/bash
# q_boyer.sh: Christian Boyer's 2a95266 (the #401 fix in Han's cold-pool PR) applied as is to develop (q/devA with
# SAMF restored), print-only dbg4 + dbgeta2 + dbg4_shal; hafs_global_1nest_atm: 20 x 6 h and 10 x 48 h (progsigma
# false, as the RT), 10 x 48 h with progsigma true.
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; Q=$P/q; H=$P/hafs_exp; PH=UFSATM/ccpp/physics; n=devB; T=$Q/$n
[ -e $T ] && { echo "$n exists"; exit 1; }
rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $Q/devA/ $T/ || exit 1
git -C $T/$PH checkout -q -- physics/CONV/SAMF/samfdeepcnv.f physics/CONV/SAMF/samfshalcnv.f
[ -z "$(git -C $T/$PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "SAMF not restored"; exit 1; }
git -C $T/$PH apply $H/boyer_2a95266.patch || { echo "patch"; exit 1; }
[ "$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF | awk '{a+=$1; d+=$2} END {print a" "d}')" = "9 5" ] || { echo "diff size"; exit 1; }
git -C $T/$PH diff -- physics/CONV/SAMF > $Q/boyer_$n.diff
d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f
awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta2_deep.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; while((getline l < e)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f
awk -v s=$H/dbg4_shal.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $s > $s.new && mv $s.new $s
sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
x=$T/tests/fv3_hafsw_intel.exe
echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $x 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL\|DBGETA')"
[ -f $x ] || { echo "NO EXE"; exit 1; }
for v in $(seq 1000 -1 981); do ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
  $H/mkexp.sh q_${n}_c$v $x "" "$ed" | tail -1; done
for v in $(seq 1000 -1 991); do ed=""; [ $v != 1000 ] && ed="s/consv_te *= *1\.$/consv_te = 0.$v/"
  $H/mkexp_long.sh q_${n}_L$v $x 48 "$ed" | tail -1
  $H/mkexp_psl.sh q_${n}ps_L$v $x 48 "$ed" | tail -1; done
echo "BOYER LAUNCHED $(date -Is)"
