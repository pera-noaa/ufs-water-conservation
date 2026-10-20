#!/usr/bin/env python3
"""Bit-compare every variable of two runs' history files (default atmf024 and sfcf024, all six tiles); prints differing variables.
Usage: python3 instrument_wb_ka_bitcmp.py <RUNDIR_A> <RUNDIR_B> [HHH=024]"""
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
h = sys.argv[3] if len(sys.argv) > 3 else "024"
nvar = ndiff = 0
for kind in ("atmf", "sfcf"):
    for t in range(1, 7):
        fa, fb = Dataset(f"{a}/{kind}{h}.tile{t}.nc"), Dataset(f"{b}/{kind}{h}.tile{t}.nc")
        for v in fa.variables:
            x, y = np.asarray(fa[v][:]), np.asarray(fb[v][:])
            nvar += 1
            if x.shape != y.shape or not np.array_equal(x, y, equal_nan=x.dtype.kind == "f"):
                ndiff += 1
                d = np.nanmax(np.abs(x.astype(float) - y.astype(float))) if x.shape == y.shape else "shape"
                print(f"DIFF {kind}{h}.tile{t} {v}: max|d| {d}")
print(f"{'BIT-IDENTICAL' if ndiff == 0 else 'DIFFERENT'}: {nvar} variables compared, {ndiff} differ ({a} vs {b}, f{h})")
