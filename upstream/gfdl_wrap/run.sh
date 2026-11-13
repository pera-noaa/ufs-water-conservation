#!/bin/bash
# run.sh REV: build the GFDL MP v3 wrapper and module at REV (nmsplit/repo) and run the column test
set -eu
G=$(cd "$(dirname "$0")" && pwd); R=$G/../nmsplit/repo; REV=$1
B=$G/build.$REV; rm -rf $B; mkdir -p $B; cd $B
for f in physics/hooks/machine.F physics/hooks/physcons.F90 physics/MP/GFDL/module_gfdlmp_param.F90 \
         physics/MP/GFDL/v3_2022/gfdl_cloud_microphys_v3_mod.F90 physics/MP/GFDL/v3_2022/gfdl_cloud_microphys_v3.F90; do
  git -C $R show $REV:$f > $(basename $f); done
cp $G/input.nml .
gfortran -cpp -O0 -g -fcheck=bounds -ffree-line-length-none -fdefault-real-8 -fdefault-double-8 machine.F physcons.F90 module_gfdlmp_param.F90 \
  gfdl_cloud_microphys_v3_mod.F90 gfdl_cloud_microphys_v3.F90 $G/test_gmp.F90 -o t.x 2>&1 | grep -i "error" -A3 | head -20
./t.x 2>&1 | grep -v "^ *=\+ *$\|gfdl_cloud_microphysics_nml_v3"
