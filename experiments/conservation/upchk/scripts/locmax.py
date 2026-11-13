#!/usr/bin/env python3
"""locmax.py <runA> <runB> <stem> <var> : location and values of max |B-A| over tiles (k, j, i), plus each run's extremes."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b, f, v = sys.argv[1:5]
best = (0, None)
for t in range(1, 7):
    x = np.asarray(Dataset(f"{a}/{f}.tile{t}.nc")[v][:], dtype=float)[0]
    y = np.asarray(Dataset(f"{b}/{f}.tile{t}.nc")[v][:], dtype=float)[0]
    d = np.abs(y - x); i = np.unravel_index(np.argmax(d), d.shape)
    if d[i] > best[0]:
        best = (d[i], (t,) + tuple(int(q) for q in i), x[i], y[i], x.min(), x.max(), y.min(), y.max())
print(f"max|d| {best[0]:.4g} at tile,k,j,i {best[1]}: A {best[2]:.5g} B {best[3]:.5g}")
for t in range(1, 7):
    for r in (a, b):
        x = np.asarray(Dataset(f"{r}/{f}.tile{t}.nc")[v][:], dtype=float)[0]
        if x.max() > 330 or x.min() < 150:
            print(f"  {r} tile {t} extreme {v}: min {x.min():.5g} max {x.max():.5g}")
