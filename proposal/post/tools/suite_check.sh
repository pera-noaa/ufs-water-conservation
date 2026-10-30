#!/bin/bash
# suite_check.sh WM_DIR REF RUNDIR: changed tests (REF:tests/test_changes.list) vs the microphysics each run's suite calls.
W=$1 REF=$2 R=$3
chg=$(git -C $W show $REF:tests/test_changes.list | awk '{print $1"_"$2}')
A=$(git -C $W ls-tree $REF UFSATM | awk '{print $3}')
mp_of(){ git -C $W/UFSATM show $A:ccpp/suites/suite_$1.xml 2>/dev/null | grep -oE '<scheme>(mp_thompson|mp_tempo|gfdl_cloud_microphys[a-z0-9_]*|mp_nssl|zhaocarr[a-z_]*|m_micro|mp_fer_hires)</scheme>' | sed 's/<[^>]*>//g' | sort -u | tr '\n' ,; }
declare -A MP
n=0; nc=0
for d in $R/*_intel $R/*_gnu; do
  t=$(basename $d); s=$(grep -hoE "ccpp_suite *= *'[^']+'" $d/input.nml 2>/dev/null | head -1 | sed "s/.*'\(.*\)'/\1/")
  [ -z "$s" ] && s=$(grep -hoE "config_physics_suite *= *'[^']+'" $d/namelist.atmosphere 2>/dev/null | head -1 | sed "s/.*'\(.*\)'/\1/")
  [ -z "$s" ] && { [ -e $d/input.nml ] || continue; s=NOSUITE; }
  [ -z "${MP[$s]+x}" ] && MP[$s]=$(mp_of $s)
  m=${MP[$s]}; n=$((n+1)); c=0; echo "$chg" | grep -qx "$t" && { c=1; nc=$((nc+1)); }
  case $m in *thompson*|*tempo*) th=1;; *) th=0;; esac
  [ $c = 1 ] && [ $th = 0 ] && echo "CHANGED, no Thompson/TEMPO: $t suite=$s mp=$m"
  [ $c = 0 ] && [ $th = 1 ] && echo "UNCHANGED, Thompson/TEMPO: $t suite=$s mp=$m"
done
echo "runs with a suite: $n, of them changed: $nc; list entries: $(echo "$chg" | wc -l)"
for t in $chg; do [ -d $R/$t ] || echo "listed but no run dir: $t"; done
echo "suites seen:"; for s in "${!MP[@]}"; do echo "  $s: ${MP[$s]}"; done | sort
