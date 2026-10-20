#!/usr/bin/env python3
"""Where do two runs differ: per model level, max |d| of a variable over 6 tiles (top 12 levels by max).
Usage: cmp_where.py <runA> <runB> <atmfFFF> <var>"""
import sys
import numpy as np
from netCDF4 import Dataset
a, b, f, v = sys.argv[1:5]
mx = None
for t in range(1, 7):
    x = Dataset(f"{a}/{f}.tile{t}.nc").variables[v][:].astype(np.float64)[0]
    y = Dataset(f"{b}/{f}.tile{t}.nc").variables[v][:].astype(np.float64)[0]
    m = np.abs(y - x).reshape(x.shape[0], -1).max(axis=1)
    c = (np.abs(y - x).reshape(x.shape[0], -1) > 1e-6).sum(axis=1)
    mx = m if mx is None else np.maximum(mx, m)
    cnt = c if t == 1 else cnt + c
order = np.argsort(mx)[::-1][:12]
for k in order:
    print(f"level {k:3d} (0=top) max|d| {mx[k]:.3e}  n(|d|>1e-6) {cnt[k]}")
print("levels with any |d|>1e-6:", int((cnt > 0).sum()), "of", len(cnt))
