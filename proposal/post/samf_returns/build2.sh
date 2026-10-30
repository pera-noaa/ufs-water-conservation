#!/bin/bash
# build.sh <variant> <samfdeepcnv source>: compile deps, the variant and the driver into bv_<variant>/drv
set -e
d=bv_$1; mkdir -p $d; cd $d
FC="gfortran -O0 -g -fcheck=all -ffpe-trap=invalid,zero,overflow -fallow-argument-mismatch -cpp -I. -J."
S=../${SRC:-src403}
$FC -c $S/machine.F; for f in mo_conv_kind.F90 physcons.F90 funcphys.f90 progsigma_calc.f90 progomega_calc.f90; do $FC -ffree-line-length-none -c $S/$f; done
$FC -c $S/samfaerosols.F; $FC -c ../$2 -o samfdeepcnv.o
$FC -ffree-line-length-none ../${DRV:-drv.f90} *.o -o drv 2>&1 | grep -v 'ld: warning' || true
ls -la drv | awk '{print "built", $NF}'
