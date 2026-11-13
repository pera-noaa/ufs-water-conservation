#!/usr/bin/env python3
"""All variables of one history file pair (tile 1..6): which differ, max|d| and max|ref|, sorted by max|d|/max|ref|.
Usage: cmp_allvars.py <runA> <runB> <file stem e.g. sfcf018> [n=25]"""
import sys
import numpy as np
from netCDF4 import Dataset
a, b, f = sys.argv[1:4]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 25
res = {}
for t in range(1, 7):
    da, db = Dataset(f"{a}/{f}.tile{t}.nc"), Dataset(f"{b}/{f}.tile{t}.nc")
    for v in da.variables:
        if v not in db.variables or da.variables[v].ndim < 2 or da.variables[v].dtype.kind not in "fiu":
            continue
        x = np.asarray(da.variables[v][:], dtype=np.float64)
        y = np.asarray(db.variables[v][:], dtype=np.float64)
        d = float(np.nanmax(np.abs(y - x)))
        r = float(np.nanmax(np.abs(x)))
        p = res.get(v, (0.0, 0.0))
        res[v] = (max(p[0], d), max(p[1], r))
diff = sorted(((d / (r or 1.0), v, d, r) for v, (d, r) in res.items() if d > 0), reverse=True)
print(f"{len(diff)} of {len(res)} variables differ")
for rel, v, d, r in diff[:n]:
    print(f"{v:16s} max|d| {d:.3e}  max|x| {r:.3e}  rel {rel:.2e}")
