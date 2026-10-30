#!/bin/bash
# rebuild_0b_c.sh: track 0b relinked onto the rule-cleaned branches (pr1-samf-c, pr1-noahmp-2c, pr1-gfdlmp-wc; comments
# and messages only), then the rt_x0b log committed on WM pr1-0b. Old heads kept as *-before-c.
set -eu
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; PH=$S/UFSATM/ccpp/physics; AT=$S/UFSATM; WM=$S
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"; RT=$P/rt_x0b/tests
IDA=(env GIT_AUTHOR_NAME="Ash Pera" GIT_AUTHOR_EMAIL=ashley.pera@noaa.gov GIT_COMMITTER_NAME="Ash Pera" GIT_COMMITTER_EMAIL=ashley.pera@noaa.gov)
r() { git -C $PH rev-parse "$1"; }
OLDP=$(r pr1-0b); OLDA=$(git -C $AT rev-parse pr1-0b); OLDW=$(git -C $WM rev-parse pr1-0b); BASE=$(r 9b65688c)
[ ${OLDP:0:8} = 9e6ec22c ] && [ ${OLDA:0:8} = fc9d2380 ] && [ ${OLDW:0:8} = dc907cc2 ] || { echo "GATE: input heads ${OLDP:0:8} ${OLDA:0:8} ${OLDW:0:8}"; exit 1; }
[ "$(git -C $PH log -1 --format=%P $OLDP)" = "$BASE $(r 3e5a4f09) $(r 93ded54e) $(r 0423ea54)" ] || { echo "GATE: old merge parents"; exit 1; }
[ "$(git -C $AT rev-parse $OLDA:ccpp/physics)" = $OLDP ] && [ "$(git -C $WM rev-parse $OLDW:UFSATM)" = $OLDA ] || { echo "GATE: old gitlinks"; exit 1; }
for x in "$PH pr1-0b" "$AT pr1-0b" "$WM pr1-0b"; do set -- $x; [ "$(git -C $1 rev-parse --abbrev-ref HEAD)" != $2 ] || { echo "GATE: $2 checked out in $1"; exit 1; }; done
for b in f5a9fc81:pr1-samf-c 5e5770b2:pr1-noahmp-2c 552b1d54:pr1-gfdlmp-wc; do
  [ "$(r ${b#*:} | cut -c1-8)" = ${b%%:*} ] || { echo "GATE: ${b#*:} not ${b%%:*}"; exit 1; }; done
# code equality with comments stripped (Fortran ! comments outside strings; blank lines dropped)
cat > $P/codecmp.py <<'PYE'
import subprocess, sys
repo, a, b = sys.argv[1:4]
def git(*x): return subprocess.run(["git", "-C", repo, *x], capture_output=True, text=True, check=True).stdout
def strip(t):
    out = []
    for ln in t.split("\n"):
        q = None; cut = len(ln)
        for i, ch in enumerate(ln):
            if q:
                if ch == q: q = None
            elif ch in "'\"": q = ch
            elif ch == "!": cut = i; break
        s = ln[:cut].rstrip()
        if s.strip(): out.append(s)
    return out
bad = []
for f in git("diff", "--name-only", a, b).split():
    ta = git("show", f"{a}:{f}") if f in git("ls-tree", "-r", "--name-only", a, "--", f) else ""
    tb = git("show", f"{b}:{f}") if f in git("ls-tree", "-r", "--name-only", b, "--", f) else ""
    fort = f.lower().endswith((".f90", ".f", ".inc"))
    if (strip(ta) if fort else ta) != (strip(tb) if fort else tb): bad.append(f)
print("CODE-DIFF:", " ".join(bad) if bad else "none")
PYE
# octopus merge, same message
TMP=$(mktemp -d $P/rbc.XXXX); trap "git -C $PH worktree remove --force $TMP/wt 2>/dev/null; rm -rf $TMP; git -C $PH worktree prune" EXIT
git -C $PH worktree add -q --detach $TMP/wt $BASE; W=$TMP/wt
git -C $PH log -1 --format=%B $OLDP > $TMP/msg
"${IDA[@]}" git -C $W merge -q --no-ff -F $TMP/msg pr1-samf-c pr1-noahmp-2c pr1-gfdlmp-wc
NEWP=$(git -C $W rev-parse HEAD)
[ "$(git -C $PH log -1 --format=%P $NEWP)" = "$BASE $(r pr1-samf-c) $(r pr1-noahmp-2c) $(r pr1-gfdlmp-wc)" ] || { echo "GATE: new merge parents"; exit 1; }
echo "merge diff vs old: $(git -C $PH diff --shortstat $OLDP $NEWP)"
c=$($PY $P/codecmp.py $PH $OLDP $NEWP); echo "new vs old: $c"; [ "$c" = "CODE-DIFF: none" ] || { echo "GATE: code differs"; exit 1; }
k=$($PY $P/codecmp.py $PH $(r pr1-0b-before-gw) $NEWP); echo "known-bad (01847384 vs new): $k"; [ "$k" != "CODE-DIFF: none" ] || { echo "GATE: known-bad passed"; exit 1; }
# ufsatm: same commit with the gitlink swapped
idx=$TMP/idx; GIT_INDEX_FILE=$idx git -C $AT read-tree $OLDA
GIT_INDEX_FILE=$idx git -C $AT update-index --cacheinfo 160000,$NEWP,ccpp/physics
t=$(GIT_INDEX_FILE=$idx git -C $AT write-tree)
NEWA=$(git -C $AT log -1 --format=%B $OLDA | "${IDA[@]}" GIT_AUTHOR_DATE="$(git -C $AT log -1 --format=%aI $OLDA)" git -C $AT commit-tree $t -p $(git -C $AT rev-parse $OLDA^))
[ "$(git -C $AT diff --name-only $OLDA $NEWA)" = ccpp/physics ] && [ "$(git -C $AT rev-parse $NEWA:ccpp/physics)" = $NEWP ] || { echo "GATE: ufsatm relink"; exit 1; }
# WM: bump commit with the gitlink swapped, then the RT log commit
idx2=$TMP/idx2; GIT_INDEX_FILE=$idx2 git -C $WM read-tree $OLDW
GIT_INDEX_FILE=$idx2 git -C $WM update-index --cacheinfo 160000,$NEWA,UFSATM
t=$(GIT_INDEX_FILE=$idx2 git -C $WM write-tree)
NEWB=$(git -C $WM log -1 --format=%B $OLDW | "${IDA[@]}" GIT_AUTHOR_DATE="$(git -C $WM log -1 --format=%aI $OLDW)" git -C $WM commit-tree $t -p $(git -C $WM rev-parse $OLDW^))
[ "$(git -C $WM diff --name-only $OLDW $NEWB)" = UFSATM ] || { echo "GATE: WM relink"; exit 1; }
for f in logs/RegressionTests_hercules.log test_changes.list; do
  h=$(git -C $WM hash-object -w $RT/$f); GIT_INDEX_FILE=$idx2 git -C $WM update-index --add --cacheinfo 100644,$h,tests/$f; done
t=$(GIT_INDEX_FILE=$idx2 git -C $WM write-tree)
NEWW=$(git -C $WM log -1 --format=%B b839573d | "${IDA[@]}" git -C $WM commit-tree $t -p $NEWB)
[ "$(git -C $WM diff --name-only $NEWB $NEWW | tr '\n' ' ')" = "tests/logs/RegressionTests_hercules.log tests/test_changes.list " ] || { echo "GATE: RT log commit files"; exit 1; }
[ "$(git -C $WM show $NEWW:tests/test_changes.list | md5sum)" = "$(md5sum < $RT/test_changes.list)" ] || { echo "GATE: test_changes.list"; exit 1; }
[ "$(git -C $WM diff --name-only 3e48f4cc $NEWW | tr '\n' ' ')" = ".gitmodules UFSATM tests/logs/RegressionTests_hercules.log tests/test_changes.list " ] || { echo "GATE: WM vs develop: $(git -C $WM diff --name-only 3e48f4cc $NEWW | tr '\n' ' ')"; exit 1; }
for x in "$AT $NEWA" "$WM $NEWB" "$WM $NEWW"; do set -- $x
  [ "$(git -C $1 log -1 --format='%an <%ae>|%cn <%ce>' $2)" = "Ash Pera <ashley.pera@noaa.gov>|Ash Pera <ashley.pera@noaa.gov>" ] || { echo "GATE: identity $2"; exit 1; }; done
git -C $PH branch -f pr1-0b-before-c $OLDP; git -C $PH branch -f pr1-0b $NEWP
git -C $AT branch -f pr1-0b-before-c $OLDA; git -C $AT branch -f pr1-0b $NEWA
git -C $WM branch -f pr1-0b-before-c $OLDW; git -C $WM branch -f pr1-0b $NEWW
echo "REBUILT: physics pr1-0b ${NEWP:0:8} (old ${OLDP:0:8}), ufsatm ${NEWA:0:8} (old ${OLDA:0:8}), WM ${NEWW:0:8} = bump ${NEWB:0:8} + RT log (old ${OLDW:0:8})"
