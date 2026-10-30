#!/bin/bash
# Usage: CC=/path/to/gcc ./run.sh   — reproduces the spurious FE_OVERFLOW.
cd "$(dirname "$0")"
CC=${CC:-gcc}
$CC -v 2>&1 | tail -1
grep -qw avx512vl /proc/cpuinfo || echo "WARNING: CPU lacks avx512vl"
for fl in "-O3 -mavx512vl" "-O3 -march=icelake-client" "-O3 -mavx512f" "-O2 -mavx512vl" \
          "-O3 -mavx512vl -ffp-contract=off" "-O3 -mavx2 -mfma" "-O0"; do
  $CC $fl condfma.c -o t.x -lm || continue
  printf '%-36s %s\n' "$fl" "$(./t.x 2>&1 | head -1)"
done
$CC -O3 -mavx512vl condfma.c -o t.x -lm && { ./t.x trap >/dev/null 2>&1; echo "-O3 -mavx512vl, feenableexcept: exit $? (136 = SIGFPE)"; }
$CC -O3 -mavx512vl -S condfma.c -o condfma.s
$CC -O3 -mavx512vl -c condfma.c -o /dev/null -fdump-tree-optimized=condfma.optimized
echo "-- GIMPLE"; grep -E '\.COND_FMA|\.MASK_LOAD' condfma.optimized | head -4
echo "-- asm";   awk '/^f:/{p=1} p&&/vfmadd|vblendm|vmovupd.*\{%k|kmov|vpcmp/' condfma.s | head -8
