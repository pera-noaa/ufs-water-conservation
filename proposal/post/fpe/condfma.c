/* -ftrapping-math: masked-off lanes must not raise FP exceptions. */
#define _GNU_SOURCE
#include <fenv.h>
#include <stdio.h>

__attribute__((noipa)) void
accum (double *restrict buf, const double *restrict x, double *restrict y,
       const int *restrict m, double w, double miss, int n)
{
  for (int i = 0; i < n; i++)
    {
#ifndef NO_Y
      y[i] = x[i];                /* makes the x load unconditional */
#endif
      if (m[i])
        buf[i] = buf[i] + x[i] * w;
      else
        buf[i] = miss;
    }
}

#define N 64
int main (void)
{
  static double buf[N], x[N], y[N];
  static int m[N];
  for (int i = 0; i < N; i++)
    {
      m[i] = (i % 2 == 0);
      x[i] = m[i] ? 1.0 : 1e307;  /* masked off; 1e307*1800 overflows */
    }
  feclearexcept (FE_ALL_EXCEPT);
  accum (buf, x, y, m, 1800.0, -1e34, N);
  int ovf = fetestexcept (FE_OVERFLOW) != 0;
  printf ("FE_OVERFLOW %s", ovf ? "RAISED" : "clear");
  return 0;
}
