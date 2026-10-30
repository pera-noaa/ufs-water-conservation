#!/bin/bash
# attr_p0d.sh: p0c with the alternative density/layer-depth form in Thompson (thdz_edit.py alt); same 9 tests, vs develop baselines and vs p0c
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; A=$P/attr; PY=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
PH=UFSATM/ccpp/physics; FV=UFSATM/fv3/atmos_cubed_sphere; NM=NOAHMP-interface/noahmp; M=physics/MP/Thompson/module_mp_thompson.F90
u=p0d; k=141; T=$A/$u; C=$A/p0c
[ -e "$T" ] && { echo "EXISTS $T, stop"; exit 1; }
cp -a $P/grp $T || exit 1
rm -rf "${T:?}"/tests/build_fv3_* "${T:?}"/tests/fv3_*.exe "${T:?}"/tests/lock
co() { git -C $T/$1 checkout -q -f "$2" && git -C $T/$1 clean -q -fdx >/dev/null; }
git -C $T checkout -q -f $(git -C $C rev-parse HEAD)
for r in $PH $FV UFSATM $NM; do
  git -C $T/$r checkout -q --detach
  git -C $T/$r fetch -q --no-recurse-submodules $C/$r $(git -C $C/$r rev-parse HEAD) || { echo "FETCH FAIL $r"; exit 1; }
  co $r $(git -C $C/$r rev-parse HEAD)
done
for r in . $PH $FV UFSATM $NM; do
  [ "$(git -C $T/$r rev-parse HEAD)" = "$(git -C $C/$r rev-parse HEAD)" ] || { echo "GATE: $r HEAD != p0c"; exit 1; }
done
$PY -I $P/thdz_edit.py alt $T/$PH/$M || exit 1
ch=$(git -C $T/$PH status --short | tr '\n' ' ')
[ "$ch" = " M $M " ] || { echo "GATE: physics changes: $ch"; exit 1; }
echo "=== $u: p0c physics $(git -C $C/$PH rev-parse --short HEAD) + alt: $(git -C $T/$PH diff --shortstat)"
md5sum $T/$PH/$M
cd $T/tests || exit 1
cp $C/tests/p0.conf p0.conf
sed -i 's/\$(( \$(id -u) + 1500 ))/$(( $(id -u) + 1500 + ${ECF_OFF:-0} ))/' rt.sh
echo "p0.conf: $(grep -c ^COMPILE p0.conf) compiles, $(grep -c ^RUN p0.conf) runs; port lines patched: $(grep -c 'ECF_OFF' rt.sh)"
cat > $A/run_$u.sbatch <<EOS
#!/bin/bash
#SBATCH -A lpdm -p service -n 1 -t 08:00:00 -J ufs_attr_$u
#SBATCH -o $A/run_$u.%j.log
# p0c + alternative Thompson density/layer-depth form; 9 tests vs develop baselines
export MACHINE_ID=hercules
export PATH=\$(echo "\$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
export ECF_OFF=$k
export dprefix=$A/rt_$u
mkdir -p \${dprefix}/stmp
cd $T/tests
./rt.sh -a lpdm -e -k -l p0.conf
echo "=== RT_EXIT rc=\$? ==="
EOS
id=$(sbatch --parsable $A/run_$u.sbatch)
echo "SUBMITTED $u=$id $(date -Is)"
