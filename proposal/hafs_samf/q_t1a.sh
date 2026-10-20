#!/bin/bash
# q/t1a: pristine develop clone + track 1a only (pr1-samf, -noahmp, -seaice_nsst, -gfdlmp merged; ufsatm SAMF32; noahmp 09b;
# FV3 at develop) + print-only dbg4 in SAMF; build; 3 members (consv_te 1, 0.999, 0.998)
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; Q=$P/q; H=$P/hafs_exp; T=$Q/t1a
PH=UFSATM/ccpp/physics
[ -e $T ] && { echo "t1a exists"; exit 1; }
rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/ufs-weather-model/ $T/ || exit 1
for r in $PH UFSATM NOAHMP-interface/noahmp; do
  git -C $T/$r fetch -q --no-recurse-submodules $S/$r "+refs/heads/pr1-*:refs/heads/pr1-*" || { echo "fetch fail $r"; exit 1; }
done
git -C $T/UFSATM checkout -q pr1-round1 && git -C $T/NOAHMP-interface/noahmp checkout -q pr1-round1 || { echo "checkout fail"; exit 1; }
for b in pr1-samf pr1-noahmp pr1-seaice_nsst pr1-gfdlmp; do
  git -C $T/$PH -c user.name=attr -c user.email=attr@localhost merge -q --no-edit $b >/dev/null 2>&1 || { echo "MERGE CONFLICT $b"; exit 1; }
done
pin=$(git -C $P/ufs-weather-model/$PH rev-parse HEAD)
[ "$(git -C $T/$PH diff --name-only $pin HEAD | wc -l)" = 16 ] || { echo "ccpp files vs pin != 16"; exit 1; }
[ "$(git -C $T/UFSATM/fv3/atmos_cubed_sphere rev-parse HEAD)" = "$(git -C $P/ufs-weather-model/UFSATM/fv3/atmos_cubed_sphere rev-parse HEAD)" ] || { echo "fv3 not at develop"; exit 1; }
d=$T/$PH/physics/CONV/SAMF
echo "t1a: physics $(git -C $T/$PH rev-parse --short HEAD) fv3 $(git -C $T/UFSATM/fv3/atmos_cubed_sphere rev-parse --short HEAD) ufsatm $(git -C $T/UFSATM rev-parse --short HEAD) noahmp $(git -C $T/NOAHMP-interface/noahmp rev-parse --short HEAD); SA1 $(grep -c 'cloud-base face' $d/samfdeepcnv.f) CFL $(grep -c 'sub-cloud eta can exceed' $d/samfdeepcnv.f) D3A $(grep -c 'releases hfus' $d/samfdeepcnv.f) CA $(grep -c caon $d/samfdeepcnv.f)"
for x in deep:samfdeepcnv shal:samfshalcnv; do f=$d/${x#*:}.f
  awk -v s=$H/dbg4_${x%%:*}.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f; done
echo "dbg: $(grep -c 'DBGSAMF\|DBGSHAL' $d/samfdeepcnv.f $d/samfshalcnv.f | tr '\n' ' ')"
sed -e "s#q/r37/#q/t1a/#g; s#q/r37\$#q/t1a#; s/hx_build_qr37 /hx_build_qt1a /; s#compile_r37#compile_t1a#g" $Q/compile_r37.sbatch > $Q/compile_t1a.sbatch
echo "compile card r37 leftovers: $(grep -c r37 $Q/compile_t1a.sbatch)"
j=$(sbatch --parsable $Q/compile_t1a.sbatch); echo "build $j"
while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
grep -h BUILD_RC $Q/compile_t1a.$j.log; x=$T/tests/fv3_hafsw_intel.exe; [ -f $x ] || { echo "NO EXE"; exit 1; }
echo "dbg strings $(strings $x | grep -c 'DBGSAMF\|DBGSHAL')"
$H/mkexp.sh q_t1a_c1000 $x | tail -1
for v in 999 998; do $H/mkexp.sh q_t1a_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; done
echo "T1A LAUNCHED $(date -Is)"
