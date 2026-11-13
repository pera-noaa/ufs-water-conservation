#!/usr/bin/env python3
"""Compare every variable of atmfHHH/sfcfHHH tiles between two run dirs: bit-identical or max |diff| per variable.
Usage: python3 fix_writeback_cmp.py <RUNDIR_A> <RUNDIR_B> <HHH> [HHH ...]"""
import sys

import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
for hh in sys.argv[3:]:
    ndiff, worst = 0, []
    for kind in ("atmf", "sfcf"):
        for t in range(1, 7):
            da, db = Dataset(f"{a}/{kind}{hh}.tile{t}.nc"), Dataset(f"{b}/{kind}{hh}.tile{t}.nc")
            for v in da.variables:
                x, y = np.asarray(da[v][:]), np.asarray(db[v][:])
                fl = np.issubdtype(x.dtype, np.floating)
                if x.shape != y.shape or not np.array_equal(x, y, equal_nan=fl):
                    ndiff += 1
                    if x.shape == y.shape and np.issubdtype(x.dtype, np.floating):
                        worst.append((float(np.nanmax(np.abs(x.astype(float) - y.astype(float)))), f"{kind}.t{t}.{v}"))
    print(f"f{hh}: {'BIT-IDENTICAL (all variables, atmf+sfcf, 6 tiles)' if ndiff == 0 else f'{ndiff} variables differ'}")
    for d, n in sorted(worst, reverse=True)[:6]:
        print(f"   {n}: max|diff| {d:.3e}")
