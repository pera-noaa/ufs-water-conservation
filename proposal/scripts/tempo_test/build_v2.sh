#!/bin/bash
# build.sh <tag> <version> <module_mp_tempo_main.F90> [inst]: TEMPO library with Makefile.gfortran defaults + closure test
R=/private/tmp/claude-33310/-Users-pera-Documents-ash-code-tm5-zoom/ec8c50fd-c8e3-44ff-8b44-bb076a72dd87/scratchpad/tempo_round2
tag=$1; v=$2; main=$3; inst=$4
B=$R/build/$tag; mkdir -p $B
cp -r $R/base/$v/src $R/base/$v/test $R/base/$v/Makefile.gfortran $B/
cp $main $B/src/module_mp_tempo_main.F90
DEF=""; [ "$v" = 9adf9ef ] && DEF="-DPRE305"
if [ -n "$inst" ]; then python3 $R/test/instrument.py $B/src/module_mp_tempo_main.F90 >/dev/null || exit 1; DEF="$DEF -DWCD"; fi
cd $B && make -f Makefile.gfortran tempo_tests > make.log 2>&1 || { echo "MAKE FAILED $tag"; grep -i -B2 -A5 error make.log | head -30; exit 1; }
FL="-g -O0 -fbacktrace -fcheck=all -ffree-line-length-0 -fdefault-real-8 -fdefault-double-8"
gfortran $FL $DEF -I./src -o wct $R/test/water_closure_test_v2.F90 libtempo.a > test_build.log 2>&1 || { echo "TEST BUILD FAILED $tag"; cat test_build.log; exit 1; }
grep -ci "warning" make.log | sed "s/^/$tag warnings: /"
echo "built $tag"
