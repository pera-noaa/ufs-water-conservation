#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 -n 1 -t 00:15:00 -J c_chk
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy/logs/chk.%j.log
# compile-check the patched files no ATM build compiles: sfc_ocean.F (E1) and NOAA-EMC/noahmp's module_sf_noahmplsm (E2),
# with b1's CCPP flags and modules; objects and .mod go to xfer/chk only
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; T=$C/b1/ufs-weather-model; B=$T/tests/build_fv3_c_b1
module use $T/modulefiles; module load ufs_hercules.intel
D=$C/xfer/chk; mkdir -p $D; cd $D
FL=$(grep "^Fortran_FLAGS" $B/UFSATM/ccpp/CMakeFiles/fv3ccpp.dir/flags.make | head -1 | cut -d= -f2-)
echo "FLAGS: $FL"
for f in $T/UFSATM/ccpp/physics/physics/SFC_Models/Ocean/UFS/sfc_ocean.F $T/NOAHMP-interface/noahmp/src/module_sf_noahmplsm.F90 $C/n0/ufs-weather-model/NOAHMP-interface/noahmp/src/module_sf_noahmplsm.F90; do
  mpiifort $FL -I$B/UFSATM/ccpp -module $D -c $f -o $D/x.o > $D/out.txt 2>&1; echo "$f rc=$? errors=$(grep -c 'error #' $D/out.txt)"; grep "error #" $D/out.txt | head -5
done
