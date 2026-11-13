/* Masked-off lanes of an if-converted FMA raise FP exceptions.
   The x86 cond_fma expander emits an unmasked FMA and a blend, so the
   multiply-add runs on lanes where m[i] == 0, which the source never
   computes.  Under the default -ftrapping-math that is wrong code:
   FE_OVERFLOW is set (and SIGFPE is raised with traps enabled).  */

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
