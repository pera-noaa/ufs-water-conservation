#!/bin/bash
# dz_setup.sh: Thompson density/layer-depth forms on the full10 base with the suites meter: dzO (ours, base), dzB (density fix reverted), dzA (alternative)
set -eu
S=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/suites
M=UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90
for t in dzO dzB dzA; do [ -e $S/$t ] && { echo "ABORT: $S/$t exists"; exit 1; }; done
bash $S/tools/mk_tree.sh dzO meter
bash $S/tools/mk_tree.sh dzB meter TH4rev_v1
bash $S/tools/mk_tree.sh dzA meter TH45alt_v1
O=$S/dzO/ufs-weather-model; B=$S/dzB/ufs-weather-model; A=$S/dzA/ufs-weather-model
cmp -s $O/$M $S/base/ufs-weather-model/$M || { echo "GATE: dzO Thompson != base"; exit 1; }
for x in $B $A; do
  d=$(diff -rq -x .git $O $x | grep -v "$M" || true); [ -z "$d" ] || { echo "GATE: $x differs elsewhere: $d"; exit 1; }
done
echo "dzB vs dzO: $(diff $O/$M $B/$M | grep -c '^[<>]') lines; dzA vs dzB: $(diff $B/$M $A/$M | grep -c '^[<>]') lines"
grep -c "rhon = " $B/$M | sed 's/^/dzB rhon assignments (expect 0): /'
grep -c "dzl(k) = dml(k)/rho(k)" $A/$M | sed 's/^/dzA dz resets (expect 3): /'
j=$(sbatch --parsable -J dz --export=NONE,TREES="dzO dzB dzA" $S/tools/build.sbatch); echo "BUILD SUBMITTED $j"
