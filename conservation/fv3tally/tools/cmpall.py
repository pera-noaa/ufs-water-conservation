#!/usr/bin/env python3
"""cmpall.py <dirA> <dirB> <stem> [n] : every numeric variable of <stem>.tile1..6.nc (e.g. atmf024, RESTART/fv_core.res):
how many differ, and the largest max|d| (relative to max|A|). Bitwise = '0 of N variables differ'."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b, f = sys.argv[1:4]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
res = {}
for t in range(1, 7):
    with Dataset(f"{a}/{f}.tile{t}.nc") as da, Dataset(f"{b}/{f}.tile{t}.nc") as db:
        for v in da.variables:
            if v not in db.variables or da.variables[v].ndim < 2 or da.variables[v].dtype.kind not in "fiu":
                continue
            x = np.asarray(da.variables[v][:], dtype=np.float64)
            y = np.asarray(db.variables[v][:], dtype=np.float64)
            eq = np.array_equal(x, y, equal_nan=True)
            d = 0.0 if eq else float(np.nanmax(np.abs(y - x)))
            if not eq and d == 0.0:
                d = float('nan')
            r = float(np.nanmax(np.abs(x)))
            p = res.get(v, (0.0, 0.0))
            res[v] = (max(p[0], d) if d == d else d, max(p[1], r))
diff = sorted((((d / (r or 1.0)) if d == d else 9e99, v, d, r) for v, (d, r) in res.items() if d != 0), reverse=True)
print(f"{f}: {len(diff)} of {len(res)} variables differ")
for rel, v, d, r in diff[:n]:
    print(f"  {v:16s} max|d| {d:.3e}  max|A| {r:.3e}  rel {rel:.2e}")
