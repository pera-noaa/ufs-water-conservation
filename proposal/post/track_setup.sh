#!/bin/bash
# track_setup.sh <0b|0c>: per-track ccpp-physics, ufsatm and WM branches (noahmp stays at develop) in a fresh RT tree rt_t<T>,
# gated, copied back to series; then submit that track's full rt.sh vs develop baselines
set -eu
T=$1
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; R=$P/rt_t$T
G=(git -c "user.name=Ash Pera" -c user.email=ashley.pera@noaa.gov)
TR=$'\n\nPart of a water-conservation project for UFS physics (NOAA GML / CIRES).\n\nAI-assisted: written with Claude Opus 5.5; reviewed by author'
PHYS_BASE=d9b70feba915022424b35aa0ab33535b9b8c6571; ATM_BASE=aa0ba811; WM_BASE=f1d68949
case $T in
  0b) BR="pr1-samf pr1-noahmp pr1-gfdlmp"; WHAT="SAMF + PBL, Noah-MP, GFDL MP v3" ;;
  0c) BR="pr1-thompson pr1-tempo"; WHAT="Thompson, TEMPO driver" ;;
  *) echo "track?"; exit 1 ;;
esac
[ -e "$R" ] && { echo "$R exists"; exit 1; }
rsync -a --exclude '/tests/*.exe' --exclude '/tests/logs/log_hercules/' "$P/rt2/" "$R/"
echo "copied: $(du -sh $R | cut -f1)"

# ccpp-physics: the track's PR branches merged on ufs/dev
cd $R/UFSATM/ccpp/physics
git fetch -q --update-head-ok $S/UFSATM/ccpp/physics '+refs/heads/pr1-*:refs/heads/pr1-*'
for b in pr1-0b pr1-0c; do git -C $S/UFSATM/ccpp/physics rev-parse -q --verify $b >/dev/null && git fetch -q $S/UFSATM/ccpp/physics +$b:$b || true; done
git checkout -q -B pr1-$T $PHYS_BASE
"${G[@]}" merge -q --no-ff -m "Merge the round-1 track-$T branches ($WHAT) for the ufsatm submodule bump$TR" $BR
for b in $BR; do git merge-base --is-ancestor $b pr1-$T || { echo "GATE: $b not in pr1-$T"; exit 1; }; done
echo "physics pr1-$T $(git rev-parse --short HEAD): $(git diff --name-only $PHYS_BASE HEAD | wc -l) files"

# ufsatm: (0b: SAMF32 build fix) + ccpp-physics bump; .gitmodules at the fork branch while the PR is open
cd $R/UFSATM
git fetch -q --update-head-ok $S/UFSATM '+refs/heads/pr1-round1:refs/heads/pr1-round1'
git checkout -q -B pr1-$T $ATM_BASE
FV3PIN=$(git ls-tree $ATM_BASE fv3/atmos_cubed_sphere | awk '{print $3}')
git -C fv3/atmos_cubed_sphere checkout -q $FV3PIN
[ $T = 0b ] && "${G[@]}" cherry-pick -q 554f8b9
git config -f .gitmodules submodule.ccpp/physics.url https://github.com/pera-noaa/ccpp-physics
git config -f .gitmodules submodule.ccpp/physics.branch pr1-$T
git add .gitmodules ccpp/physics
"${G[@]}" commit -q -m "Update ccpp-physics for the round-1 conservation bug fixes, track $T ($WHAT)$TR"

# noahmp: develop's pin (phase 0 has no noahmp change)
cd $R/NOAHMP-interface/noahmp
NMPIN=$(git -C $R ls-tree $WM_BASE NOAHMP-interface/noahmp | awk '{print $3}')
git checkout -q $NMPIN

# WM: submodule bumps; .gitmodules at the fork branches
cd $R
git checkout -q -- tests/logs/RegressionTests_hercules.log tests/test_changes.list
git checkout -q -B pr1-$T $WM_BASE
git config -f .gitmodules submodule.UFSATM.url https://github.com/pera-noaa/ufsatm
git config -f .gitmodules submodule.UFSATM.branch pr1-$T
git add UFSATM
SUBJ="Update UFSATM"
git add .gitmodules
"${G[@]}" commit -q -m "$SUBJ for the round-1 conservation bug fixes, track $T ($WHAT)$TR"

# gates: every gitlink equals its checked-out HEAD; nothing outside the track
bad=0
for r in UFSATM/ccpp/physics UFSATM/fv3/atmos_cubed_sphere UFSATM NOAHMP-interface/noahmp; do
  have=$(git -C $R/$r rev-parse HEAD); p=$(dirname $r); b=$(basename $r); [ "$p" = . ] && par=$R || par=$R/$p
  link=$(git -C $par ls-tree HEAD $b | awk '{print $3}')
  [ "$link" = "$have" ] || { echo "GATE: $r gitlink $link != HEAD $have"; bad=1; }
done
[ "$(git -C $R/UFSATM ls-tree HEAD fv3/atmos_cubed_sphere | awk '{print $3}')" = "$FV3PIN" ] || { echo "GATE: fv3 not develop"; bad=1; }
[ "$(git -C $R ls-tree HEAD NOAHMP-interface/noahmp | awk '{print $3}')" = "$NMPIN" ] || { echo "GATE: noahmp not develop"; bad=1; }
echo "WM changed: $(git -C $R diff --name-only $WM_BASE HEAD | tr '\n' ' ')"
echo "ufsatm changed: $(git -C $R/UFSATM diff --name-only $ATM_BASE HEAD | tr '\n' ' ')"
echo "dirty: $(git -C $R status --porcelain --ignore-submodules=none | grep -v '^??' | wc -l)"
[ $bad = 0 ] || exit 1

# copy the branches back to series
git -C $S/UFSATM/ccpp/physics fetch -q $R/UFSATM/ccpp/physics +pr1-$T:pr1-$T
git -C $S/UFSATM fetch -q $R/UFSATM +pr1-$T:pr1-$T
git -C $S fetch -q $R +pr1-$T:pr1-$T
echo "series has pr1-$T: physics $(git -C $S/UFSATM/ccpp/physics rev-parse --short pr1-$T) ufsatm $(git -C $S/UFSATM rev-parse --short pr1-$T) wm $(git -C $S rev-parse --short pr1-$T)"

# ecflow port offset (run tree only, not committed) so the two tracks' rt.sh do not share a server
sed -i 's/\$(( \$(id -u) + 1500 ))/$(( $(id -u) + 1500 + ${ECF_OFF:-0} ))/' $R/tests/rt.sh
echo "ECF_OFF lines: $(grep -c 'ECF_OFF' $R/tests/rt.sh)"

case $T in 0b) OFF=21; NODE=hercules-dtn-2 ;; 0c) OFF=22; NODE=hercules-dtn-3 ;; esac
sed -e "s#rt_final4#rt_t$T#g" -e "s#/rt2/tests#/rt_t$T/tests#" -e "s/-t 08:00:00/-t 16:00:00/" \
    -e "s/^# FINAL:.*/# track $T: full suite on the WM pr1-$T branch, vs develop baselines, no -c; this log goes in the WM PR/" \
    -e "s/^export MACHINE_ID=hercules/export MACHINE_ID=hercules\nexport ECF_OFF=$OFF/" $P/rt_final4.sbatch > $P/rt_t$T.sbatch
grep -q "rt_t$T/tests" $P/rt_t$T.sbatch && grep -q "ECF_OFF=$OFF" $P/rt_t$T.sbatch || { echo "GATE: sbatch edit"; exit 1; }
j=$(sbatch --parsable --nodelist=$NODE $P/rt_t$T.sbatch)
echo "TRACK $T SUBMITTED $j"
