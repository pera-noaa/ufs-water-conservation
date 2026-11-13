#!/bin/bash
# Build the NM12 harness for each variant. Run on a compute node (sbatch build.sbatch).
set -e
N=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/nm12
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/p20rt_final/ufs-weather-model/UFSATM/ccpp/physics/physics
module purge
module use /work2/noaa/co2/ash/ufs-chem-v1/upstream/p20rt_final/ufs-weather-model/modulefiles
module load ufs_hercules.intel
FC=${FC:-mpiifort}
FLAGS="-fpp -DCCPP -real-size 64 -O2 -fp-model precise -fno-alias -align all -ftz -traceback -convert big_endian -assume byterecl"
NC="-I${netcdf_fortran_ROOT:-$NETCDF_FORTRAN}/include"
NCL="-L${netcdf_fortran_ROOT:-$NETCDF_FORTRAN}/lib -lnetcdff"
for v in ${VARIANTS:-pristine orig fix neg}; do
  B=$N/build/$v; mkdir -p $B; cd $B; rm -f *.o *.mod
  $FC $FLAGS -c $P/hooks/machine.F
  $FC $FLAGS -c $P/hooks/physcons.F90
  $FC $FLAGS -c $P/tools/funcphys.f90
  $FC $FLAGS -c $P/SFC_Models/Land/Noah/namelist_soilveg.f
  $FC $FLAGS -c $P/SFC_Models/Land/Noah/set_soilveg.f
  $FC $FLAGS -c $P/SFC_Layer/UFS/sfc_diff.f
  $FC $FLAGS -c $N/src/noahmp_tables.f90
  $FC $FLAGS -c $N/variants/$v/module_sf_noahmplsm.F90
  $FC $FLAGS -c $N/variants/$v/module_sf_noahmp_glacier.F90
  $FC $FLAGS $NC -c $N/src/lnd_iau_mod.F90
  $FC $FLAGS -c $N/src/noahmpdrv.F90
  $FC $FLAGS -c $N/harness/hv_mod.F90
  D=""; [ $v = pristine ] && D=-DPRISTINE   # pristine: no meter in the model, local arrays stay zero
  $FC $FLAGS $D -I$N/harness -c $N/harness/nm12_main.F90
  $FC $FLAGS -o nm12_$v.x *.o $NCL
  echo "BUILT $v"
done
