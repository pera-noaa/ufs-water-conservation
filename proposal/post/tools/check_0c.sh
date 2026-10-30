#!/bin/bash
# check_0c.sh: track 0c branches (series) = fresh merge of the posted PR heads; pointers consistent.
set -u
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/series
P=$S/UFSATM/ccpp/physics A=$S/UFSATM W=$S
TH=0e22f8c2 TP=bd82d044 DEV=9b65688c ADEV=c9c98451 WDEV=3e48f4cc
bad=0; ok(){ echo "ok   $*"; }; no(){ echo "FAIL $*"; bad=1; }
full(){ git -C $1 rev-parse $2; }
# physics: fresh octopus merge in a temporary worktree
T=$S/../chk0c_wt; git -C $P worktree remove --force $T 2>/dev/null; rm -rf $T
git -C $P worktree add -q --detach $T $DEV
git -C $T -c user.name=x -c user.email=x merge -q --no-edit $TH $TP >/dev/null 2>&1 || no "fresh merge conflicts"
fresh=$(git -C $T rev-parse HEAD^{tree})
[ "$fresh" = "$(full $P pr1-0c^{tree})" ] && ok "physics pr1-0c tree = fresh merge of $DEV+$TH+$TP" || no "physics tree differs: $(git -C $P diff --stat $fresh pr1-0c | tail -1)"
# known-bad: the pre-693 merge must fail the same comparison
[ "$fresh" != "$(full $P 549f8716^{tree})" ] && ok "known-bad 549f8716 differs ($(git -C $P diff --shortstat 549f8716 $fresh))" || no "known-bad not caught"
git -C $P worktree remove --force $T
echo "     549f8716..pr1-0c:"; git -C $P diff -U0 549f8716 pr1-0c | grep '^[+-][^+-]' | sed 's/^/       /'
# ufsatm: parent, gitlink, .gitmodules, nothing else
[ "$(full $A pr1-0c^)" = "$(full $A $ADEV)" ] && ok "ufsatm parent = $ADEV" || no "ufsatm parent $(git -C $A rev-parse --short=8 pr1-0c^)"
gl=$(git -C $A ls-tree pr1-0c ccpp/physics | awk '{print $3}')
[ "$gl" = "$(full $P pr1-0c)" ] && ok "ufsatm gitlink ccpp/physics = physics pr1-0c" || no "ufsatm gitlink ${gl:0:8}"
echo "     ufsatm files changed vs $ADEV: $(git -C $A diff --name-only $ADEV pr1-0c | tr '\n' ' ')"
git -C $A show pr1-0c:.gitmodules | grep -A3 'ccpp/physics"' | grep -E 'url|branch' | sed 's/^/     /'
# WM: develop is an ancestor, gitlinks, files
git -C $W merge-base --is-ancestor $WDEV pr1-0c && ok "WM develop $WDEV is an ancestor" || no "WM base"
gl=$(git -C $W ls-tree pr1-0c UFSATM | awk '{print $3}')
[ "$gl" = "$(full $A pr1-0c)" ] && ok "WM gitlink UFSATM = ufsatm pr1-0c" || no "WM gitlink ${gl:0:8}"
others=$(git -C $W diff --name-only $WDEV pr1-0c | grep -vxE 'UFSATM|\.gitmodules|tests/logs/RegressionTests_hercules\.log|tests/test_changes\.list')
[ -z "$others" ] && ok "WM changes only UFSATM, .gitmodules, RT log, test_changes.list" || no "WM also changes: $others"
git -C $W show pr1-0c:.gitmodules | grep -A3 'UFSATM"' | grep -E 'url|branch' | sed 's/^/     /'
echo "     RT log names: $(git -C $W show pr1-0c:tests/logs/RegressionTests_hercules.log | grep -oE 'ccpp-physics[^ ]* [0-9a-f]{7,}|[0-9a-f]{8,} [^ ]*physics' | head -3 | tr '\n' ' ')"
git -C $W show pr1-0c:tests/logs/RegressionTests_hercules.log | grep -iE 'physics|ufsatm' | head -4 | sed 's/^/     /'
echo "     test_changes.list: $(git -C $W show pr1-0c:tests/test_changes.list | wc -l) lines"
[ $bad = 0 ] && echo "ALL OK" || echo "CHECK FAILED"
