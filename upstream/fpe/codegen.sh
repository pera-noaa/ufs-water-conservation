#!/bin/bash
# Compile FMS diag_manager.F90 as spack-stack 1.9.2 did; report masked-loop codegen.
set -u
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/fms_codegen
FC=/apps/contrib/spack-stack/gnu/installs/gnu/13.3.0/bin/gfortran
M=/apps/contrib/spack-stack/spack-stack-1.9.2/envs/ue-gcc-13.3.0/install/gcc/13.3.0/fms-2024.02-anubnpi/include_r8
S=$W/FMS-2024.02
DEFS="-DENABLE_QUAD_PRECISION -DGFS_CONSTANTS -DGFS_PHYS -DHAVE_GETTID -DINTERNAL_FILE_NML -Duse_deprecated_io -Duse_libMPI -Duse_netCDF"
INC="-I$S/include -I$S/fms -I$S/fms/include -I$S/fms2_io/include -I$S/string_utils/include -I$S/mpp/include -I$S/diag_manager/include -I$M -I/apps/contrib/spack-stack/spack-stack-1.9.2/envs/ue-gcc-13.3.0/install/gcc/13.3.0/netcdf-fortran-4.6.1-o3vqo5m/include -I/apps/contrib/spack-stack/openmpi/installs/openmpi/4.1.6/include -I/apps/contrib/spack-stack/openmpi/installs/openmpi/4.1.6/lib"
BASE="-fcray-pointer -fconvert=big-endian -ffree-line-length-none -fno-range-check -fbacktrace -fPIC -fdefault-real-8 -fdefault-double-8 -fallow-argument-mismatch -w -fopenmp"
cd $W
build() { # tag, extra flags
  mkdir -p b_$1 && cd b_$1
  $FC $DEFS $INC $BASE $2 -J. -c $S/diag_manager/diag_manager.F90 -o dm.o 2>&1 | tail -3
  objdump -d --no-show-raw-insn dm.o | awk '/<__diag_manager_mod_MOD_diag_send_data>:/{f=1} f&&/^$/{exit} f' > dsd.s
  n_fma=$(grep -c 'vfmadd...pd' dsd.s); n_mfma=$(grep -E 'vfmadd...pd' dsd.s | grep -c '{%k'); n_blend=$(grep -c 'vblendmpd\|vblendvpd' dsd.s); n_mload=$(grep -E 'vmovupd.*\{%k|vmaskmovpd' dsd.s | wc -l)
  echo "$1: fma=$n_fma masked_fma=$n_mfma blend=$n_blend masked_loads=$n_mload"
  cd $W
}
build exact "-O3 -funroll-all-loops -finline-functions -march=icelake-client -mtune=icelake-client"
build avx2  "-O3 -funroll-all-loops -finline-functions -march=haswell"
build sse2  "-O3 -funroll-all-loops -finline-functions"
build o2    "-O2 -march=icelake-client"
build notrap_vec "-O3 -funroll-all-loops -finline-functions -march=icelake-client -mtune=icelake-client -fno-tree-loop-if-convert"
# compare with the shipped object
ar x /apps/contrib/spack-stack/spack-stack-1.9.2/envs/ue-gcc-13.3.0/install/gcc/13.3.0/fms-2024.02-anubnpi/lib/libfms_r8.a diag_manager.F90.o
objdump -d --no-show-raw-insn diag_manager.F90.o | awk '/<__diag_manager_mod_MOD_diag_send_data>:/{f=1} f&&/^$/{exit} f' > shipped.s
echo "shipped vs exact: $(diff <(sed 's/^ *[0-9a-f]*://' shipped.s) <(sed 's/^ *[0-9a-f]*://' b_exact/dsd.s) | grep -c '^[<>]') differing lines of $(wc -l < shipped.s)"
