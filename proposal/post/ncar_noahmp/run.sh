#!/bin/bash
# run.sh REV PREC: build the v5 modules at REV and run the harness (PREC = double or single)
set -eu
T=$(cd "$(dirname "$0")" && pwd); R=$T/../noahmp; REV=$1; PREC=$2
B=$T/build.$(echo $REV | tr / _).$PREC; rm -rf $B; mkdir -p $B; cd $B
git -C $R show $REV:utility/Machine.F90 > Machine.F90
for m in ConstantDefineMod ConfigVarType ForcingVarType EnergyVarType WaterVarType BiochemVarType NoahmpVarType \
         SnowLayerWaterComboMod SnowLayerCombineMod SnowThermalPropertyMod; do git -C $R show $REV:src/$m.F90 > $m.F90; done
FL="-cpp -O0 -g -fcheck=all -ffpe-trap=invalid,zero,overflow"
[ $PREC = double ] && FL="$FL -DDOUBLE_PREC -fdefault-real-8"
gfortran $FL Machine.F90 ConstantDefineMod.F90 ConfigVarType.F90 ForcingVarType.F90 EnergyVarType.F90 WaterVarType.F90 \
  BiochemVarType.F90 NoahmpVarType.F90 SnowLayerWaterComboMod.F90 SnowLayerCombineMod.F90 SnowThermalPropertyMod.F90 \
  $T/test_snow_heat.F90 -o t.x 2>&1 | grep -v "^$" | grep -iv "warning" | head -20
./t.x
