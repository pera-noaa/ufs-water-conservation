#!/usr/bin/env python3
"""rmsdiff.py <runA> <runB> [hour=024] : rms and mean of B - A for T (atmf tmp, all levels), ps (atmf pressfc),
LH (sfcf lhtfl_ave), over all cells of the 6 tiles (C96 cells are near-equal area)."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1:3]
h = sys.argv[3] if len(sys.argv) > 3 else '024'
for stem, v, lab in [('atmf', 'tmp', 'T (K)'), ('atmf', 'pressfc', 'ps (Pa)'), ('sfcf', 'lhtfl_ave', 'LH (W m-2)')]:
    d = []
    for t in range(1, 7):
        with Dataset(f'{a}/{stem}{h}.tile{t}.nc') as da, Dataset(f'{b}/{stem}{h}.tile{t}.nc') as db:
            d.append((np.asarray(db[v][:], dtype=np.float64) - np.asarray(da[v][:], dtype=np.float64)).ravel())
    d = np.concatenate(d)
    print(f'{lab:11s} rms {np.sqrt(np.mean(d*d)):.4g}  mean {np.mean(d):+.3g}  max|d| {np.max(np.abs(d)):.3g}')
