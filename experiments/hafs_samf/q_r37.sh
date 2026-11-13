#!/bin/bash
# q/r37: pristine develop clone + the 37-fix branches (pr1-round1 everywhere) + print-only dbg4 in SAMF; build; 3 members
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; Q=$P/q; H=$P/hafs_exp; T=$Q/r37
[ -e $T ] && { echo "r37 exists"; exit 1; }
rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/ufs-weather-model/ $T/ || exit 1
for r in UFSATM/ccpp/physics UFSATM/fv3/atmos_cubed_sphere UFSATM NOAHMP-interface/noahmp; do
  git -C $T/$r fetch -q $S/$r "+refs/heads/pr1-round1:refs/heads/pr1-round1" && git -C $T/$r checkout -q pr1-round1 || { echo "checkout fail $r"; exit 1; }
  [ "$(git -C $T/$r rev-parse HEAD)" = "$(git -C $S/$r rev-parse pr1-round1)" ] || { echo "head mismatch $r"; exit 1; }
done
d=$T/UFSATM/ccpp/physics/physics/CONV/SAMF
echo "r37: physics $(git -C $T/UFSATM/ccpp/physics rev-parse --short HEAD) fv3 $(git -C $T/UFSATM/fv3/atmos_cubed_sphere rev-parse --short HEAD) ufsatm $(git -C $T/UFSATM rev-parse --short HEAD) noahmp $(git -C $T/NOAHMP-interface/noahmp rev-parse --short HEAD); SA1 $(grep -c 'cloud-base face' $d/samfdeepcnv.f) CFL $(grep -c 'sub-cloud eta can exceed' $d/samfdeepcnv.f) D3A $(grep -c 'releases hfus' $d/samfdeepcnv.f) CA $(grep -c caon $d/samfdeepcnv.f)"
for x in deep:samfdeepcnv shal:samfshalcnv; do f=$d/${x#*:}.f
  awk -v s=$H/dbg4_${x%%:*}.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f; done
echo "dbg: $(grep -c 'DBGSAMF\|DBGSHAL' $d/samfdeepcnv.f $d/samfshalcnv.f | tr '\n' ' ')"
sed -e "s#q/fv3/#q/r37/#g; s#q/fv3\$#q/r37#; s/hx_build_qfv3 /hx_build_qr37 /; s#compile_fv3#compile_r37#g" $Q/compile_fv3.sbatch > $Q/compile_r37.sbatch
j=$(sbatch --parsable $Q/compile_r37.sbatch); echo "build $j"
while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
grep -h BUILD_RC $Q/compile_r37.$j.log; x=$T/tests/fv3_hafsw_intel.exe; [ -f $x ] || { echo "NO EXE"; exit 1; }
$H/mkexp.sh q_r37_c1000 $x | tail -1
for v in 999 998; do $H/mkexp.sh q_r37_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; done
echo "R37 LAUNCHED"
