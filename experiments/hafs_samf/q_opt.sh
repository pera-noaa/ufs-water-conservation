#!/bin/bash
# q_opt.sh: SAMF fix options A (sub-cloud CFL bound), D (CFL bound in every updraft layer), E (vapour positivity bound on xmb)
# on develop and on the 24-fix set (t1a); print-only dbg4 as in q_t1a.sh; 20 members each (consv_te 1 ... 0.981)
set -u
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; S=$P/series; Q=$P/q; H=$P/hafs_exp
PH=UFSATM/ccpp/physics; FV=UFSATM/fv3/atmos_cubed_sphere
members() { local n=$1 x=$Q/$1/tests/fv3_hafsw_intel.exe v
  [ -f $x ] || { echo "$n: NO EXE"; return 1; }
  for v in $(seq 1000 -1 981); do
    if [ $v = 1000 ]; then $H/mkexp.sh q_${n}_c1000 $x | tail -1
    else $H/mkexp.sh q_${n}_c$v $x "" "s/consv_te *= *1\.$/consv_te = 0.$v/" | tail -1; fi
  done; }
build() { # <tree> <base dev|t1a> <option A|D|E>
  local n=$1 base=$2 opt=$3 T=$Q/$1 pin d f j want=0
  [ -e $T ] && { echo "$n exists"; return 1; }
  rsync -a --exclude 'build_*' --exclude 'tests/fv3_*.exe' $P/ufs-weather-model/ $T/ || return 1
  if [ $base = t1a ]; then
    for r in $PH UFSATM NOAHMP-interface/noahmp; do
      git -C $T/$r fetch -q --no-recurse-submodules $S/$r "+refs/heads/pr1-*:refs/heads/pr1-*" || { echo "$n: fetch fail $r"; return 1; }
    done
    git -C $T/UFSATM checkout -q pr1-round1 && git -C $T/NOAHMP-interface/noahmp checkout -q pr1-round1 || { echo "$n: checkout fail"; return 1; }
    for b in pr1-samf pr1-noahmp pr1-seaice_nsst pr1-gfdlmp; do
      git -C $T/$PH -c user.name=attr -c user.email=attr@localhost merge -q --no-edit $b >/dev/null 2>&1 || { echo "$n: MERGE CONFLICT $b"; return 1; }
    done; want=16
  fi
  pin=$(git -C $P/ufs-weather-model/$PH rev-parse HEAD)
  [ "$(git -C $T/$PH diff --name-only $pin HEAD | wc -l)" = $want ] || { echo "$n: ccpp files vs pin != $want"; return 1; }
  [ "$(git -C $T/$FV rev-parse HEAD)" = "$(git -C $P/ufs-weather-model/$FV rev-parse HEAD)" ] || { echo "$n: fv3 not at develop"; return 1; }
  d=$T/$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f
  case $opt in
    A|D) [ "$(grep -c 'xmbmax(i) = dp / (real(grav, kind=conv_wp)' $f)" = 1 ] || { echo "$n: anchor"; return 1; }
         awk -v s=$H/opt$opt.f '{print} /xmbmax\(i\) = dp \/ \(real\(grav, kind=conv_wp\)/{g=1} g==1 && /^      enddo/{while((getline l < s)>0) print l; g=2}' $f > $f.new && mv $f.new $f;;
    E)   [ "$(grep -c '^          xmb(i) = min(xmb(i),xmbmax(i))$' $f)" = 1 ] || { echo "$n: anchor"; return 1; }
         awk -v s=$H/optE.f '{print} /^          xmb\(i\) = min\(xmb\(i\),xmbmax\(i\)\)$/{g=1} g==1 && /^      enddo/{while((getline l < s)>0) print l; g=2}' $f > $f.new && mv $f.new $f;;
  esac
  echo "$n: base $base option $opt inserted $(grep -c "option $opt\|sub-cloud eta can exceed 1" $f); physics $(git -C $T/$PH rev-parse --short HEAD) fv3 $(git -C $T/$FV rev-parse --short HEAD) ufsatm $(git -C $T/UFSATM rev-parse --short HEAD); diff +$(git -C $T/$PH diff --numstat -- physics/CONV/SAMF/samfdeepcnv.f | cut -f1)"
  for x in deep:samfdeepcnv shal:samfshalcnv; do g=$d/${x#*:}.f
    awk -v s=$H/dbg4_${x%%:*}.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $g > $g.new && mv $g.new $g; done
  sed -e "s#q/r37/#q/$n/#g; s#q/r37\$#q/$n#; s/hx_build_qr37 /hx_build_q$n /; s#compile_r37#compile_$n#g" $Q/compile_r37.sbatch > $Q/compile_$n.sbatch
  j=$(sbatch --parsable $Q/compile_$n.sbatch); echo "$n: build $j"
  while squeue -j $j -h 2>/dev/null | grep -q .; do sleep 60; done
  echo "$n: $(grep -h BUILD_RC $Q/compile_$n.$j.log); dbg strings $(strings $T/tests/fv3_hafsw_intel.exe 2>/dev/null | grep -c 'DBGSAMF\|DBGSHAL')"
  members $n
}
for spec in devA:dev:A devD:dev:D devE:dev:E t1aA:t1a:A t1aD:t1a:D t1aE:t1a:E; do
  IFS=: read n b o <<< "$spec"; build $n $b $o > $Q/opt_$n.log 2>&1 &
done
wait
cat $Q/opt_*.log | grep -v "^q_"
echo "OPT LAUNCHED $(date -Is)"
