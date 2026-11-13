/* { dg-do run } */
/* { dg-require-effective-target avx512vl } */
/* { dg-require-effective-target fenv_exceptions } */
/* { dg-options "-O3 -mavx512vl" } */

#include <fenv.h>
#include <stdlib.h>

#define N 64

__attribute__((noipa)) void
f (double *restrict a, const double *restrict b, double *restrict c,
   const int *restrict m, double w, double e, int n)
{
  for (int i = 0; i < n; i++)
    {
      c[i] = b[i];
      if (m[i])
	a[i] = a[i] + b[i] * w;
      else
	a[i] = e;
    }
}

int
main (void)
{
  static double a[N], b[N], c[N];
  static int m[N];
  if (!__builtin_cpu_supports ("avx512vl"))
    return 0;
  for (int i = 0; i < N; i++)
    {
      m[i] = i & 1;
      b[i] = m[i] ? 1.0 : 1e307;
    }
  feclearexcept (FE_ALL_EXCEPT);
  f (a, b, c, m, 1800.0, -1e34, N);
  if (fetestexcept (FE_OVERFLOW))
    abort ();
  return 0;
}
