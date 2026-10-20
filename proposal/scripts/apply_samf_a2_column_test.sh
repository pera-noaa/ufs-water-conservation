#!/bin/bash
# Build and run apply_samf_a2_column_test.f90 against one samfdeepcnv.f (gfortran, default reals promoted to 8 bytes); METERED if it carries instrument_wb_ka.py's meter.
# Usage: bash apply_samf_a2_column_test.sh <samfdeepcnv.f> <dir with v1 machine/physcons/funcphys/progsigma/samfaerosols .o/.mod>
set -e
F=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); D=$(cd "$2" && pwd); H=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; cd "$W"
cp "$D"/*.mod .
M=""; grep -q "wka_kdt" "$F" && M="-DMETERED"
cp "$F" s.f
gfortran -O0 -fdefault-real-8 -c s.f -I"$D"
gfortran -O0 -cpp $M -c "$H/apply_samf_a2_column_test.f90" -I. -I"$D"
gfortran -o t apply_samf_a2_column_test.o s.o "$D"/machine.o "$D"/physcons.o "$D"/funcphys.o "$D"/progsigma_calc.o "$D"/samfaerosols.o
./t
