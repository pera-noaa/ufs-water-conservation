#!/bin/bash
# run.sh REV PREC: build GFDL main's gfdl_mp.F90 at REV (terminal_fall made public, test only) and run test_sedi
set -eu
T=$(cd "$(dirname "$0")" && pwd); R=$T/../gfdlfv3; REV=$1; PREC=$2
B=$T/build.$REV.$PREC; rm -rf $B; mkdir -p $B; cd $B
git -C $R show $REV:model/gfdl_mp.F90 > gfdl_mp.F90
python3 -I - gfdl_mp.F90 <<'PY'
import sys; f=sys.argv[1]; s=open(f).read()
a="    public :: gfdl_mp_init\n"; assert s.count(a)==1; open(f,"w").write(s.replace(a, a+"    public :: terminal_fall\n"))
PY
FL="-cpp -O0 -g -fcheck=all -ffpe-trap=invalid,zero,overflow -ffree-line-length-none"
[ $PREC = double ] && FL="$FL -fdefault-real-8 -fdefault-double-8"
gfortran $FL -Wall $T/fms_stub.F90 gfdl_mp.F90 $T/test_sedi.F90 -o t.x 2> build.err || { cat build.err | head; exit 1; }
echo "warnings in gfdl_mp.F90: $(grep -c 'gfdl_mp.F90.*\|Warning' build.err | head -1) lines ($(grep -c 'Warning:' build.err))"
./t.x | grep -v "^ *$"
