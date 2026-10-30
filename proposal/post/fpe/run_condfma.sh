#!/bin/bash
# condfma.c: spurious FE_OVERFLOW from gcc's AVX-512 cond_fma expansion.
CC=${CC:-gcc}
$CC -O3 -march=icelake-client condfma.c -o a.x -lm && ./a.x; echo "  [-O3 -march=icelake-client]"
$CC -O3 -march=icelake-client -ffp-contract=off condfma.c -o b.x -lm && ./b.x; echo "  [+ -ffp-contract=off]"
$CC -O0 condfma.c -o c.x -lm && ./c.x; echo "  [-O0]"
