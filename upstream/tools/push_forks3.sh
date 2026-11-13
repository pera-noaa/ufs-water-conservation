#!/bin/bash
# push_forks3.sh (push_forks2 + WM base 3e48f4cc, fork base fast-forwarded) <ccpp-physics|ufsatm|ufs-weather-model>: bring the branches from Hercules (series) as a git bundle and
# push them to the pera-noaa fork (23 Oct heads; rebased branches replace the old ones with a lease on the fork's current head). Gates: base = upstream head, base is an ancestor, identity and trailer on every
# non-merge commit. Run from anywhere; work dir in $WORK (default: a temp dir).
set -eu
R=$1
case $R in
  ccpp-physics) SUB=UFSATM/ccpp/physics; UP=ufs-community/ccpp-physics; BB=ufs/dev; BASE=9b65688ca82fad3f87801799f82d30ba7fe00007
                BR="pr1-samf pr1-noahmp pr1-gfdlmp pr1-thompson pr1-tempo pr1-0b pr1-0c" ;;
  ufsatm) SUB=UFSATM; UP=NOAA-EMC/ufsatm; BB=develop; BASE=c9c98451; BR="pr1-0b pr1-0c" ;;
  ufs-weather-model) SUB=.; UP=ufs-community/ufs-weather-model; BB=develop; BASE=3e48f4cc; BR="pr1-0b pr1-0c" ;;
  *) echo "repo?"; exit 1 ;;
esac
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1
W=${WORK:-$(mktemp -d)}/$R; mkdir -p "$W"; cd "$W"
up=$(gh api "repos/$UP/commits/$BB" -q .sha)
[ "${up:0:8}" = "${BASE:0:8}" ] || { echo "GATE: $UP $BB moved to ${up:0:8}"; exit 1; }
broker run --timeout 300 hercules -- "cd $H/series/$SUB && git bundle create $H/push_$R.bundle $BR ^$BASE >/dev/null 2>&1 && git rev-parse $BR" > heads.txt
broker run --timeout 300 hercules -- "cat $H/push_$R.bundle" > push.bundle
[ -d .git ] || git init -q
git remote get-url fork >/dev/null 2>&1 || git remote add fork "https://github.com/pera-noaa/$R"
git fetch -q --depth=1 fork "$BB"
if [ "$(git rev-parse FETCH_HEAD)" != "$up" ]; then
  # fast-forward the fork's base branch to upstream; refuse anything else
  old=$(git rev-parse FETCH_HEAD)
  git fetch -q --depth=200 "https://github.com/$UP" "$BB"
  git merge-base --is-ancestor "$old" "$up" || { echo "GATE: fork $BB ${old:0:8} is not behind upstream"; exit 1; }
  git push -q fork "$up:refs/heads/$BB" && echo "fork $BB fast-forwarded ${old:0:8} -> ${up:0:8}"
fi
git bundle verify -q push.bundle
git fetch -q push.bundle "refs/heads/*:refs/heads/*"
bad=0; i=0
for b in $BR; do
  i=$((i+1)); want=$(sed -n ${i}p heads.txt)
  [ "$(git rev-parse $b)" = "$want" ] || { echo "GATE: $b != Hercules $want"; bad=1; }
  git merge-base --is-ancestor "$up" "$b" || { echo "GATE: $b not on $BB"; bad=1; }
  for c in $(git rev-list --no-merges "$up..$b"); do
    [ "$(git log -1 --format='%an <%ae>|%cn <%ce>' $c)" = "Ash Pera <ashley.pera@noaa.gov>|Ash Pera <ashley.pera@noaa.gov>" ] || { echo "GATE: identity $c"; bad=1; }
    git log -1 --format=%B $c | grep -q "^AI-assisted: written with Claude Opus 5.5; reviewed by author$" || { echo "GATE: trailer $c"; bad=1; }
  done
  echo "$b ${want:0:8}: $(git rev-list --count $up..$b) commits on $BB"
done
[ $bad = 0 ] || exit 1
lease=""; for b in $BR; do o=$(gh api "repos/pera-noaa/$R/branches/$b" -q .commit.sha 2>/dev/null || true); [ -n "$o" ] && lease="$lease --force-with-lease=refs/heads/$b:$o"; done
git push -q $lease fork $(for b in $BR; do printf "%s:refs/heads/%s " $b $b; done)
echo "PUSHED $R: $BR"
