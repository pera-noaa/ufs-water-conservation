#!/usr/bin/env python3
"""tprof.py <runA> <runB> [hour] : level-mean and level-rms of T(B) - T(A) (atmf tmp) in pressure bands."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1:3]
h = sys.argv[3] if len(sys.argv) > 3 else '024'
d, p = [], None
for t in range(1, 7):
    with Dataset(f'{a}/atmf{h}.tile{t}.nc') as da, Dataset(f'{b}/atmf{h}.tile{t}.nc') as db:
        x = np.asarray(db['tmp'][:], dtype=np.float64) - np.asarray(da['tmp'][:], dtype=np.float64)
        d.append(x.reshape(x.shape[-3], -1))
        if p is None:
            p = np.asarray(da['pfull'][:], dtype=np.float64)
d = np.concatenate(d, axis=1)
m, r = d.mean(axis=1), np.sqrt((d*d).mean(axis=1))
for lo, hi in [(0, 1), (1, 10), (10, 50), (50, 200), (200, 500), (500, 850), (850, 1100)]:
    k = (p >= lo) & (p < hi)
    if k.any():
        print(f'{lo:5d}-{hi:<5d} hPa  levels {k.sum():3d}  mean dT {m[k].mean():+.4f}  rms dT {np.sqrt((r[k]**2).mean()):.4f}')
