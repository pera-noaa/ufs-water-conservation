# gcc Bugzilla report: filed as Bug 128221 (27 Oct 2026)

Trunk checked 24 Oct 2026 on Compiler Explorer (`cgsnapshot`, gcc 17.0.0 20261024): same codegen, runtime FAIL.
Pre-report checks run 27 Oct 2026 on Hercules (`fms_codegen/gccbz`). CE link made 27 Oct; CE's executors that day lacked AVX-512 (SIGILL), so the runtime FAIL on trunk/16.2 is from 24 Oct.

- **Product / Component:** gcc / target
- **Version:** 17.0 (trunk); also 16.2, 15.3, 14.4, 13.3, 12.2
- **Keywords:** wrong-code
- **Host / Target / Build:** x86_64-pc-linux-gnu
- **Summary:** [x86] AVX-512 cond_fma expanders compute masked-off lanes: spurious FE_OVERFLOW with -ftrapping-math
- **Known to fail:** 12.2.0, 13.3.0, 14.4.0, 15.3.0, 16.2.0, 17.0
- **See Also:** 122103, 127177
- **Attachments:** `condfma.c` (testcase), `condfma.i` (gcc 13.3.0 `-save-temps`)

---

With AVX-512, if-conversion correctly produces `.COND_FMA`, but `cond_fma<mode>` in `config/i386/sse.md` expands it as an unmasked `fma` into a temporary followed by `vec_merge` with the else value. The multiply-add is therefore evaluated in lanes whose condition is false, which raises FP exceptions the source never performs, under the default `-ftrapping-math`. `cond_fms`, `cond_fnma` and `cond_fnms` have the same shape. The expanders are unchanged on master.

Testcase (attached `condfma.c`; testsuite form `pr-condfma.c`):

```c
#define _GNU_SOURCE
#include <fenv.h>
#include <stdio.h>
#include <stdlib.h>

#define N 64

__attribute__((noipa)) void
f (double *restrict a, const double *restrict b, double *restrict c,
   const int *restrict m, double w, double e, int n)
{
  for (int i = 0; i < n; i++)
    {
      c[i] = b[i];		/* b[i] is loaded in every lane */
      if (m[i])
	a[i] = a[i] + b[i] * w;
      else
	a[i] = e;
    }
}

int
main (int argc, char **argv)
{
  static double a[N], b[N], c[N];
  static int m[N];
  (void) argv;
  for (int i = 0; i < N; i++)
    {
      m[i] = i & 1;
      b[i] = m[i] ? 1.0 : 1e307;	/* 1e307 * 1800 overflows */
    }
  if (argc > 1)
    feenableexcept (FE_OVERFLOW);
  feclearexcept (FE_ALL_EXCEPT);
  f (a, b, c, m, 1800.0, -1e34, N);
  if (fetestexcept (FE_OVERFLOW))
    {
      puts ("FAIL: FE_OVERFLOW from a masked-off lane");
      fflush (stdout);
      abort ();
    }
  puts ("PASS");
  return 0;
}
```

The product `b[i] * w` overflows only where `m[i] == 0`, where the source assigns `e` and never computes it.

`gcc -v` (13.3.0, the release built by spack-stack on Hercules, Rocky Linux 9):

```
Target: x86_64-pc-linux-gnu
Configured with: ../configure -v --prefix=/apps/contrib/spack-stack/gnu/installs/gnu/13.3.0 --with-gmp=/apps/contrib/spack-stack/gnu/installs/gmp-6.2.1 --with-mpfr=/apps/contrib/spack-stack/gnu/installs/mpfr-4.1.0 --with-mpc=/apps/contrib/spack-stack/gnu/installs/mpc-1.2.1 --with-isl=/apps/contrib/spack-stack/gnu/installs/isl-0.24 CFLAGS=' -fPIC' --disable-multilib --enable-languages=c,c++,fortran --with-system-libstdcxx
Thread model: posix
gcc version 13.3.0 (GCC)
```

Command line: `gcc -O3 -mavx512vl condfma.c -o t.x -lm && ./t.x` (`./t.x trap` enables the trap). `-Wall -Wextra` is clean, `-fno-strict-aliasing -fwrapv -fno-aggressive-loop-optimizations` still fails, and `-fsanitize=address,undefined` reports nothing at -O0 or -O3.

Results with gcc 13.3.0 and 12.2.0 (identical; Intel Xeon Platinum 8380):

```
-O3 -mavx512vl                       FAIL: FE_OVERFLOW from a masked-off lane
-O3 -march=icelake-client            FAIL: FE_OVERFLOW from a masked-off lane
-O3 -mavx512f                        FAIL: FE_OVERFLOW from a masked-off lane
-O2 -mavx512vl                       PASS
-O3 -mavx512vl -ffp-contract=off     PASS
-O3 -mavx2 -mfma                     PASS
-O0                                  PASS
-O3 -mavx512vl, feenableexcept: SIGFPE
```

On Compiler Explorer with `-O3 -mavx512vl`, trunk (17.0.0 20261027), 16.2, 15.3 and 14.4 generate the same unmasked `vfmadd213pd` + `vblendmpd`: https://godbolt.org/z/39ozdM3hr (trunk, without and with `-ffp-contract=off`). Run on an AVX-512 executor, trunk and 16.2 FAIL as above; with `-ffp-contract=off`, 16.2 and 14.4 PASS.

`-fdump-tree-optimized` (`-O3 -mavx512vl`):

```
vect_patt_51.28_125 = .COND_FMA (mask_patt_33.25_116, vect__5.13_98, vect_cst__118, vect__10.23_113, vect_cst__124);
```

Generated code: unmasked FMA, then blend:

```
vfmadd213pd   (%rdi,%rax,2), %zmm4, %zmm2
vpcmpd        $4, %zmm6, %zmm7, %k1
vblendmpd     %zmm2, %zmm3, %zmm2{%k1}
```

With `-ffp-contract=off` the same loop uses `.COND_MUL`/`.COND_ADD`, which expand masked (`vmulpd ...{%k1}{z}`, `vaddpd ...{%k1}`), and passes. AVX-512 masking suppresses exceptions on masked-off elements, so a zero-masked FMA (`*_fmadd_<mode>_maskz_1`) followed by the merge with operand 5, or a merge-masked form when operand 5 is one of the inputs, would avoid this.

Found in the wild: FMS (NOAA-GFDL) `diag_manager.F90` masked time-averaging loop (`if (mask) buffer = buffer + field*weight else buffer = missvalue`), built `-O3 -march=icelake-client` and linked into an executable compiled with `-ffpe-trap=overflow`. There the field is a merge-masked load, so the masked-off lanes hold stale register contents and the SIGFPE is intermittent.

Possibly related: PR122103 (SVE vectorisation not honouring -ftrapping-math), PR96373.
